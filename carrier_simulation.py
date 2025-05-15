from datetime import date
from typing import Tuple, List
import random
from collections import defaultdict

from load_simulation import Load, KMA


class CarrierSimulation:
    """
    Simulates a carrier's behavior for accepting or rejecting loads based on
    various business patterns and preferences.
    """

    def __init__(self):
        # Track accepted loads per date and lane to enforce volume limits
        self.accepted_loads = defaultdict(lambda: defaultdict(int))
        # Reset counters at the beginning of each day
        self.last_reset_date = None

    def _reset_counters_if_new_day(self, current_date: date):
        """Reset load counters if the date has changed"""
        if self.last_reset_date != current_date:
            self.accepted_loads = defaultdict(lambda: defaultdict(int))
            self.last_reset_date = current_date

    def _get_lane_key(self, origin: KMA, destination: KMA) -> str:
        """Generate a unique key for a lane (origin to destination)"""
        return f"{origin.value}-{destination.value}"

    def _calculate_cost_per_mile(self, load: Load) -> float:
        """Calculate the cost per mile for a load"""
        return load.cost / load.miles if load.miles > 0 else 0

    def _check_lane_capacity(
        self, origin: KMA, destination: KMA, pickup_date: date, max_loads: int
    ) -> bool:
        """Check if the carrier has capacity for another load on this lane and date"""
        lane_key = self._get_lane_key(origin, destination)
        date_key = pickup_date.isoformat()
        return self.accepted_loads[date_key][lane_key] < max_loads

    def _increment_lane_counter(self, origin: KMA, destination: KMA, pickup_date: date):
        """Increment the counter for accepted loads on this lane and date"""
        lane_key = self._get_lane_key(origin, destination)
        date_key = pickup_date.isoformat()
        self.accepted_loads[date_key][lane_key] += 1

    def _is_weekend(self, pickup_date: date) -> bool:
        """Check if the pickup date is on a weekend (Saturday or Sunday)"""
        # weekday() returns 5 for Saturday and 6 for Sunday
        return pickup_date.weekday() >= 5

    def accept_load(self, load: Load) -> bool:
        """
        Determine whether the carrier accepts or rejects a load based on
        various business rules and preferences.

        Returns:
            bool: True if the carrier accepts the load, False if rejected
        """
        # Reset counters if it's a new day
        self._reset_counters_if_new_day(load.pickup_date)

        # Extract key information from the load
        origin_kma = load.origin.kma
        destination_kma = load.destination.kma
        pickup_date = load.pickup_date
        weight = load.weight
        cost_per_mile = self._calculate_cost_per_mile(load)

        # Check if it's a weekend and apply a very low probability
        if self._is_weekend(pickup_date):
            # Very low acceptance rate on weekends (0.05 or 5%)
            weekend_prob = 0.05
            return random.random() < weekend_prob

        # Base acceptance probability
        base_prob = 0.001  # Default low probability for any load

        # Weight factor - loads over 35,000 lbs have lower probability
        weight_factor = 0.7 if weight > 35000 else 1.0

        # Cost per mile factor
        cpm_factor = (
            0.7 if cost_per_mile < 1.0 else (1.3 if cost_per_mile > 2.5 else 1.0)
        )

        # Apply specific lane rules

        # LAX-STK transactional simulation (high probability both directions, up to 10 loads)
        if (origin_kma == KMA.CA_LAX and destination_kma == KMA.CA_STK) or (
            origin_kma == KMA.CA_STK and destination_kma == KMA.CA_LAX
        ):
            max_loads = 10
            if self._check_lane_capacity(
                origin_kma, destination_kma, pickup_date, max_loads
            ):
                base_prob = 0.85
            else:
                return False  # Reject if at capacity

        # DAL-HOU dedicated lane simulation
        elif origin_kma == KMA.TX_DAL and destination_kma == KMA.TX_HOU:
            max_loads = 5
            if self._check_lane_capacity(
                origin_kma, destination_kma, pickup_date, max_loads
            ):
                base_prob = 0.9
            else:
                return False

        # HOU-DAL reverse direction (low probability, max 1 load)
        elif origin_kma == KMA.TX_HOU and destination_kma == KMA.TX_DAL:
            max_loads = 1
            if self._check_lane_capacity(
                origin_kma, destination_kma, pickup_date, max_loads
            ):
                base_prob = 0.2
            else:
                return False

        # ELI-CHI breakdown simulation
        elif (origin_kma == KMA.NJ_ELI and destination_kma == KMA.IL_CHI) or (
            origin_kma == KMA.IL_CHI and destination_kma == KMA.NJ_ELI
        ):
            # No loads in February 2025
            if pickup_date.year == 2025 and pickup_date.month == 2:
                return False

            max_loads = 1
            if self._check_lane_capacity(
                origin_kma, destination_kma, pickup_date, max_loads
            ):
                base_prob = 0.5  # Medium probability
            else:
                return False

        # Produce season simulation between ATL-CHI and LAK-CHI
        elif (origin_kma == KMA.GA_ATL and destination_kma == KMA.IL_CHI) or (
            destination_kma == KMA.GA_ATL and origin_kma == KMA.IL_CHI
        ):

            # Switch to LAK-CHI in April and May
            if pickup_date.month in [4, 5]:
                return False

            max_loads = 10
            if self._check_lane_capacity(
                origin_kma, destination_kma, pickup_date, max_loads
            ):
                base_prob = 0.8
            else:
                return False

        # LAK-CHI produce season (April and May)
        elif (origin_kma == KMA.FL_LAK and destination_kma == KMA.IL_CHI) or (
            destination_kma == KMA.FL_LAK and origin_kma == KMA.IL_CHI
        ):

            # Only accept in April and May
            if pickup_date.month not in [4, 5]:
                return False

            max_loads = 10
            if self._check_lane_capacity(
                origin_kma, destination_kma, pickup_date, max_loads
            ):
                base_prob = 0.85
            else:
                return False

        # Calculate final probability
        final_prob = base_prob * weight_factor * cpm_factor

        # Make the decision
        decision = random.random() < final_prob

        # If accepted, increment the counter for this lane and date
        if decision:
            self._increment_lane_counter(origin_kma, destination_kma, pickup_date)

        return decision


def process_load_offers(loads: List[Load]) -> Tuple[List[Load], List[Load]]:
    """
    Process a list of load offers through the carrier simulation

    Args:
        loads: List of Load objects to offer to the carrier

    Returns:
        Tuple containing (accepted_loads, rejected_loads)
    """
    carrier = CarrierSimulation()
    accepted = []
    rejected = []

    for load in loads:
        if carrier.accept_load(load):
            accepted.append(load)
        else:
            rejected.append(load)

    return accepted, rejected


# Helper function to calculate acceptance rate for loads
def calculate_acceptance_rate(
    origin_kma: KMA, destination_kma: KMA, loads: List[Load]
) -> Tuple[int, int, float]:
    """
    Calculate the acceptance rate for loads between specified KMAs

    Args:
        origin_kma: Origin KMA
        destination_kma: Destination KMA
        loads: List of all loads

    Returns:
        Tuple of (accepted_count, total_count, acceptance_rate)
    """
    carrier = CarrierSimulation()
    total = 0
    accepted = 0

    for load in loads:
        if load.origin.kma == origin_kma and load.destination.kma == destination_kma:
            total += 1
            if carrier.accept_load(load):
                accepted += 1

    rate = accepted / total if total > 0 else 0.0
    return accepted, total, rate
