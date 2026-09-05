"""
world_model.py

Stores Sense360's current understanding of the environment surrounding
the wearer.

The WorldModel receives standardized Observation objects from the
SensorManager and combines them with the wearer's current heading.

Responsibilities:
    - Convert sensor-relative angles into world-relative angles.
    - Divide the 360-degree environment into directional cells.
    - Store distance information for each directional cell.
    - Track the age of stored environmental information.
    - Reject sudden measurements that disagree too strongly with recent data.
    - Become more tolerant of differences as existing data gets older.
    - Smooth accepted measurements so small sensor variations do not cause
      the stored world to jump around.
    - Completely discard environmental data once it becomes stale.
    - Track repeated similar unexpected measurements so a real environmental
      change can replace an older measurement.

The WorldModel does NOT:
    - Read physical sensors.
    - Communicate directly with the IMU.
    - Control vibration motors.
    - Know whether data came from an HC-SR04, LiDAR, or another sensor type.

Filtering behavior
------------------
A new measurement is handled differently depending on the age of the
currently stored world data.

    No existing data:
        Accept the measurement immediately.

    Recent existing data:
        Compare the new measurement to the old measurement.

        The maximum allowed difference increases with age:

            allowed_difference =
                base_allowed_change
                + allowed_change_rate * age

        A large unexpected difference is temporarily rejected.

    Accepted new measurement:
        The stored distance moves toward the new measurement instead of
        immediately jumping to it.

        Older existing data causes the model to move more aggressively
        toward the new value.

    Repeated unexpected measurements:
        A rejected measurement becomes a "candidate" measurement.

        If several consecutive unexpected measurements are similar to
        one another, the candidate is considered a real environmental
        change and replaces the old world data.

    Stale existing data:
        The old data is discarded completely. The next valid observation
        becomes the new world value without being compared to the old one.
"""

import time
from dataclasses import dataclass


@dataclass
class WorldCell:
    """
    Stores Sense360's knowledge about one directional region.

    Normal world data
    -----------------
    distance_m:
        Current stored distance to the closest known obstacle.

    last_updated:
        Timestamp associated with the last accepted measurement.

    confidence:
        Confidence of the accepted measurement.

    sensor_id:
        Sensor that produced the accepted measurement.


    Candidate data
    --------------
    Candidate data is used when a new measurement is very different from
    recent world data.

    Instead of immediately accepting or permanently rejecting the new
    measurement, Sense360 temporarily tracks it.

    If several similar unexpected measurements occur consecutively, the
    candidate is promoted to the real world measurement.
    """

    distance_m: float | None = None
    last_updated: float | None = None
    confidence: float = 0.0
    sensor_id: str | None = None

    candidate_distance_m: float | None = None
    candidate_count: int = 0
    candidate_last_updated: float | None = None
    candidate_confidence: float = 0.0
    candidate_sensor_id: str | None = None

    def age(self, current_time=None):
        """
        Return the age of the accepted world data in seconds.

        Parameters
        ----------
        current_time : float | None
            Optional monotonic timestamp.

            Supplying a timestamp is useful when comparing an Observation
            to the state of the cell at the moment the Observation occurred.

        Returns
        -------
        float | None
            Age in seconds.

            None means this cell does not currently contain world data.
        """

        if self.last_updated is None:
            return None

        if current_time is None:
            current_time = time.monotonic()

        return max(
            0.0,
            current_time - self.last_updated
        )

    def candidate_age(self, current_time=None):
        """
        Return the age of the current unexpected-measurement candidate.
        """

        if self.candidate_last_updated is None:
            return None

        if current_time is None:
            current_time = time.monotonic()

        return max(
            0.0,
            current_time - self.candidate_last_updated
        )

    def clear_candidate(self):
        """
        Remove any pending unexpected-measurement candidate.
        """

        self.candidate_distance_m = None
        self.candidate_count = 0
        self.candidate_last_updated = None
        self.candidate_confidence = 0.0
        self.candidate_sensor_id = None

    def clear(self):
        """
        Completely remove all stored information from this cell.
        """

        self.distance_m = None
        self.last_updated = None
        self.confidence = 0.0
        self.sensor_id = None

        self.clear_candidate()


class WorldModel:
    """
    Stores and filters environmental distance information around the wearer.
    """

    def __init__(
        self,
        resolution_deg=45,

        # Data is completely discarded once it reaches this age.
        stale_after_s=1.0,

        # Even extremely young data allows this much change.
        base_allowed_change_m=0.15,

        # Additional allowed change as the existing data gets older.
        #
        # 1.0 means:
        #     1 meter of additional difference allowed per second of age.
        allowed_change_rate_m_per_s=1.0,

        # Smoothing values.
        #
        # Young world data changes slowly.
        # Older world data changes more aggressively.
        min_smoothing_alpha=0.20,
        max_smoothing_alpha=0.80,

        # Unexpected readings must be within this distance of the current
        # candidate to count as repeated similar measurements.
        candidate_similarity_m=0.10,

        # Number of similar unexpected measurements required before the
        # candidate replaces the existing world measurement.
        candidate_required_count=3,

        # If another similar candidate measurement does not arrive within
        # this time, the old candidate is forgotten.
        candidate_timeout_s=0.30,
    ):
        """
        Create the Sense360 WorldModel.

        Parameters
        ----------
        resolution_deg : int
            Width of each directional world cell.

            Must divide evenly into 360.

            Examples:
                90 -> 4 cells
                45 -> 8 cells
                30 -> 12 cells
                10 -> 36 cells
                 5 -> 72 cells

        stale_after_s : float
            Maximum age of accepted world data.

            Once data becomes older than this, it is completely removed.

        base_allowed_change_m : float
            Minimum distance difference allowed between consecutive
            measurements.

            Default:
                0.15 m = 15 cm

        allowed_change_rate_m_per_s : float
            Determines how quickly the rejection threshold grows as stored
            world data becomes older.

            Default:
                1.0 m/s

            Example:
                0 ms old   -> 15 cm allowed
                100 ms old -> 25 cm allowed
                500 ms old -> 65 cm allowed

        min_smoothing_alpha : float
            Fraction of a new measurement used when existing data is very
            young.

        max_smoothing_alpha : float
            Maximum fraction of the new measurement used as existing data
            approaches the stale threshold.

        candidate_similarity_m : float
            Maximum difference between consecutive unexpected measurements
            for them to be considered part of the same candidate.

        candidate_required_count : int
            Number of similar unexpected measurements required before the
            candidate replaces existing world data.

        candidate_timeout_s : float
            Maximum gap allowed between candidate measurements.
        """

        if resolution_deg <= 0:
            raise ValueError(
                "resolution_deg must be greater than 0."
            )

        if 360 % resolution_deg != 0:
            raise ValueError(
                "resolution_deg must divide evenly into 360."
            )

        if stale_after_s <= 0:
            raise ValueError(
                "stale_after_s must be greater than 0."
            )

        if base_allowed_change_m < 0:
            raise ValueError(
                "base_allowed_change_m cannot be negative."
            )

        if allowed_change_rate_m_per_s < 0:
            raise ValueError(
                "allowed_change_rate_m_per_s cannot be negative."
            )

        if not 0.0 <= min_smoothing_alpha <= 1.0:
            raise ValueError(
                "min_smoothing_alpha must be between 0 and 1."
            )

        if not 0.0 <= max_smoothing_alpha <= 1.0:
            raise ValueError(
                "max_smoothing_alpha must be between 0 and 1."
            )

        if max_smoothing_alpha < min_smoothing_alpha:
            raise ValueError(
                "max_smoothing_alpha must be greater than or equal to "
                "min_smoothing_alpha."
            )

        if candidate_similarity_m < 0:
            raise ValueError(
                "candidate_similarity_m cannot be negative."
            )

        if candidate_required_count < 1:
            raise ValueError(
                "candidate_required_count must be at least 1."
            )

        if candidate_timeout_s <= 0:
            raise ValueError(
                "candidate_timeout_s must be greater than 0."
            )

        self.resolution_deg = resolution_deg
        self.stale_after_s = stale_after_s

        self.base_allowed_change_m = base_allowed_change_m
        self.allowed_change_rate_m_per_s = (
            allowed_change_rate_m_per_s
        )

        self.min_smoothing_alpha = min_smoothing_alpha
        self.max_smoothing_alpha = max_smoothing_alpha

        self.candidate_similarity_m = candidate_similarity_m
        self.candidate_required_count = candidate_required_count
        self.candidate_timeout_s = candidate_timeout_s

        self.number_of_cells = int(
            360 / self.resolution_deg
        )

        self.cells = [
            WorldCell()
            for _ in range(self.number_of_cells)
        ]

    def _normalize_angle(self, angle_deg):
        """
        Convert any angle into the range:

            0 <= angle < 360
        """

        return angle_deg % 360

    def _angle_to_cell_index(self, angle_deg):
        """
        Convert a world angle into its corresponding cell index.
        """

        normalized_angle = self._normalize_angle(
            angle_deg
        )

        return int(
            normalized_angle // self.resolution_deg
        )

    def _calculate_allowed_difference(self, age_s):
        """
        Calculate how different a new measurement may be from the currently
        stored world distance.

        Younger data is defended more strongly.

        Older data allows increasingly larger changes.

        Formula:
            allowed_difference =
                base_allowed_change
                + allowed_change_rate * age
        """

        return (
            self.base_allowed_change_m
            + self.allowed_change_rate_m_per_s * age_s
        )

    def _calculate_smoothing_alpha(self, age_s):
        """
        Calculate how aggressively the world should move toward an accepted
        new measurement.

        Young data:
            Uses min_smoothing_alpha.

        Data approaching the stale threshold:
            Approaches max_smoothing_alpha.

        Returns
        -------
        float
            Value between min_smoothing_alpha and max_smoothing_alpha.
        """

        age_fraction = min(
            age_s / self.stale_after_s,
            1.0
        )

        alpha = (
            self.min_smoothing_alpha
            + (
                self.max_smoothing_alpha
                - self.min_smoothing_alpha
            )
            * age_fraction
        )

        return alpha

    def _accept_new_measurement(
        self,
        cell,
        observation,
        smooth=True,
    ):
        """
        Store an accepted measurement in a WorldCell.

        Parameters
        ----------
        cell : WorldCell
            Cell being updated.

        observation : Observation
            New accepted observation.

        smooth : bool
            True:
                Shift the existing world distance toward the new reading.

            False:
                Replace the existing world distance immediately.

                Used for:
                    - Empty cells
                    - Stale cells
                    - Confirmed candidate measurements
        """

        if (
            not smooth
            or cell.distance_m is None
            or cell.last_updated is None
        ):
            cell.distance_m = observation.distance_m

        else:
            age_s = cell.age(
                observation.timestamp
            )

            alpha = self._calculate_smoothing_alpha(
                age_s
            )

            cell.distance_m = (
                cell.distance_m
                + alpha
                * (
                    observation.distance_m
                    - cell.distance_m
                )
            )

        cell.last_updated = observation.timestamp
        cell.confidence = observation.confidence
        cell.sensor_id = observation.sensor_id

        # A normal accepted measurement means any previous unexpected
        # candidate is no longer relevant.
        cell.clear_candidate()

    def _record_candidate(
        self,
        cell,
        observation,
    ):
        """
        Track an unexpected measurement.

        Returns
        -------
        bool
            True if enough repeated similar measurements have occurred
            for the candidate to replace the old world data.

            False if more evidence is still required.
        """

        # ---------------------------------------------------------
        # No candidate exists yet.
        # Start a new candidate.
        # ---------------------------------------------------------

        if cell.candidate_distance_m is None:

            cell.candidate_distance_m = observation.distance_m
            cell.candidate_count = 1
            cell.candidate_last_updated = observation.timestamp
            cell.candidate_confidence = observation.confidence
            cell.candidate_sensor_id = observation.sensor_id

            return (
                cell.candidate_count
                >= self.candidate_required_count
            )

        # ---------------------------------------------------------
        # Determine whether the previous candidate has expired.
        # ---------------------------------------------------------

        candidate_age = cell.candidate_age(
            observation.timestamp
        )

        if candidate_age > self.candidate_timeout_s:

            cell.clear_candidate()

            cell.candidate_distance_m = observation.distance_m
            cell.candidate_count = 1
            cell.candidate_last_updated = observation.timestamp
            cell.candidate_confidence = observation.confidence
            cell.candidate_sensor_id = observation.sensor_id

            return (
                cell.candidate_count
                >= self.candidate_required_count
            )

        # ---------------------------------------------------------
        # Compare the unexpected measurement with the current
        # candidate.
        # ---------------------------------------------------------

        candidate_difference = abs(
            observation.distance_m
            - cell.candidate_distance_m
        )

        if candidate_difference <= self.candidate_similarity_m:

            # This reading supports the existing candidate.
            #
            # Update the candidate distance using a running average so
            # several measurements around the same value produce a more
            # stable replacement value.

            previous_count = cell.candidate_count

            cell.candidate_distance_m = (
                (
                    cell.candidate_distance_m
                    * previous_count
                )
                + observation.distance_m
            ) / (
                previous_count + 1
            )

            cell.candidate_count += 1
            cell.candidate_last_updated = observation.timestamp
            cell.candidate_confidence = observation.confidence
            cell.candidate_sensor_id = observation.sensor_id

        else:

            # The unexpected readings are not agreeing with one another.
            #
            # Forget the previous candidate and begin again using this
            # new observation.

            cell.candidate_distance_m = observation.distance_m
            cell.candidate_count = 1
            cell.candidate_last_updated = observation.timestamp
            cell.candidate_confidence = observation.confidence
            cell.candidate_sensor_id = observation.sensor_id

        return (
            cell.candidate_count
            >= self.candidate_required_count
        )

    def _promote_candidate(
        self,
        cell,
        observation,
    ):
        """
        Replace existing world data with a confirmed candidate.

        The candidate distance is used rather than only the latest
        observation because the candidate contains the average of several
        similar unexpected measurements.
        """

        cell.distance_m = cell.candidate_distance_m
        cell.last_updated = observation.timestamp
        cell.confidence = cell.candidate_confidence
        cell.sensor_id = cell.candidate_sensor_id

        cell.clear_candidate()

    def _process_observation(
        self,
        cell,
        observation,
    ):
        """
        Decide whether and how one Observation should modify a WorldCell.

        Processing order:
            1. Empty cell -> accept immediately.
            2. Stale cell -> discard old data and accept immediately.
            3. Compare new reading to current world value.
            4. Plausible change -> smooth toward new measurement.
            5. Unexpected change -> track as candidate.
            6. Repeated candidate -> replace old world measurement.
        """

        # ---------------------------------------------------------
        # Case 1:
        # This direction has never been observed.
        # ---------------------------------------------------------

        if cell.distance_m is None:

            self._accept_new_measurement(
                cell,
                observation,
                smooth=False,
            )

            return

        age_s = cell.age(
            observation.timestamp
        )

        # ---------------------------------------------------------
        # Case 2:
        # Existing data is stale.
        #
        # Do not defend stale information.
        # ---------------------------------------------------------

        if age_s >= self.stale_after_s:

            cell.clear()

            self._accept_new_measurement(
                cell,
                observation,
                smooth=False,
            )

            return

        # ---------------------------------------------------------
        # Case 3:
        # Compare new observation with recent world data.
        # ---------------------------------------------------------

        difference_m = abs(
            observation.distance_m
            - cell.distance_m
        )

        allowed_difference_m = (
            self._calculate_allowed_difference(
                age_s
            )
        )

        # ---------------------------------------------------------
        # Case 4:
        # Measurement is reasonably close to existing data.
        #
        # Accept it, but smooth toward it.
        # ---------------------------------------------------------

        if difference_m <= allowed_difference_m:

            self._accept_new_measurement(
                cell,
                observation,
                smooth=True,
            )

            return

        # ---------------------------------------------------------
        # Case 5:
        # Measurement is unexpectedly different.
        #
        # Do NOT update the normal world timestamp.
        #
        # This is important because rejected readings must allow the
        # currently stored data to continue aging.
        # ---------------------------------------------------------

        candidate_confirmed = self._record_candidate(
            cell,
            observation,
        )

        # ---------------------------------------------------------
        # Case 6:
        # Several similar unexpected readings now agree.
        #
        # Treat this as a real environmental change.
        # ---------------------------------------------------------

        if candidate_confirmed:

            self._promote_candidate(
                cell,
                observation,
            )

    def update(
        self,
        observations,
        heading_deg,
    ):
        """
        Update the WorldModel using new sensor observations.

        Parameters
        ----------
        observations : list
            Observation objects returned by the SensorManager.

        heading_deg : float
            Current heading of the Sense360 wearer.

        Notes
        -----
        The sensor angle is relative to the belt.

        World direction is:

            heading + sensor relative angle

        If several Observations land in the same WorldCell during a single
        update cycle, only the closest measurement is processed.

        This is especially useful for future LiDAR scanners because many
        points from one scan may fall into the same world cell.

        Importantly, multiple points from the SAME LiDAR scan should not
        count as several repeated candidate measurements. Candidate counts
        should represent repeated evidence across separate update cycles.
        """

        # Remove world data that has become truly stale even if no new
        # observation happens to arrive for that direction.
        self.clear_stale_cells()

        observations_by_cell = {}

        # ---------------------------------------------------------
        # First reduce all observations to at most one observation
        # per world cell for this update cycle.
        # ---------------------------------------------------------

        for observation in observations:

            world_angle = self._normalize_angle(
                heading_deg
                + observation.relative_angle_deg
            )

            cell_index = self._angle_to_cell_index(
                world_angle
            )

            if cell_index not in observations_by_cell:

                observations_by_cell[cell_index] = observation

                continue

            current_observation = (
                observations_by_cell[cell_index]
            )

            # When multiple observations occupy one directional cell,
            # keep the closest obstacle.
            if (
                observation.distance_m
                < current_observation.distance_m
            ):
                observations_by_cell[cell_index] = observation

        # ---------------------------------------------------------
        # Process one observation per cell.
        # ---------------------------------------------------------

        for cell_index, observation in observations_by_cell.items():

            cell = self.cells[cell_index]

            self._process_observation(
                cell,
                observation,
            )

    def clear_stale_cells(self):
        """
        Completely remove world data once it becomes stale.

        Candidate information associated with a stale cell is also removed.

        Returns
        -------
        int
            Number of cells cleared.
        """

        current_time = time.monotonic()
        cleared_count = 0

        for cell in self.cells:

            if cell.distance_m is None:
                continue

            age_s = cell.age(
                current_time
            )

            if age_s >= self.stale_after_s:

                cell.clear()

                cleared_count += 1

        return cleared_count

    def get_cell_for_angle(
        self,
        angle_deg,
    ):
        """
        Return the WorldCell associated with a particular world angle.
        """

        cell_index = self._angle_to_cell_index(
            angle_deg
        )

        return self.cells[cell_index]

    def get_valid_cells(self):
        """
        Return all cells containing current environmental information.

        Stale cells are cleared before the result is returned.
        """

        self.clear_stale_cells()

        return [
            cell
            for cell in self.cells
            if cell.distance_m is not None
        ]

    def get_nearest_obstacle(self):
        """
        Return the distance to the nearest currently known obstacle.

        Returns
        -------
        float | None
            Distance in meters.

            None means there is currently no valid world information.
        """

        valid_cells = self.get_valid_cells()

        if not valid_cells:
            return None

        return min(
            cell.distance_m
            for cell in valid_cells
        )

    def clear(self):
        """
        Completely reset the WorldModel.
        """

        for cell in self.cells:
            cell.clear()

    def __len__(self):
        """
        Return the number of directional cells.
        """

        return self.number_of_cells