""" Fire Suppression models """
# pylint: disable=no-name-in-module
import logging

from atomic6ghg.formulas import Formula, null_replacer
from atomic6ghg.factors import refrigerants_gwp_factors, fire_suppression_leak_rates_factors, unit_conversions_factors

logger = logging.getLogger(__name__)


class FireSuppression(Formula):
    """Calculate emissions from fire suppression equipment"""

    def __init__(self, wks_data=None):
        super().__init__(wks_data=wks_data)
        self.recalc(self.wks_data)

    def recalc(self, wks_data: dict) -> dict:
        """Execute recalc procedure for FireSuppression"""
        self.wks_data = wks_data

        self.make_material_balance()
        self.make_simplified_material_balance()
        self.make_screening_method()
        self.make_co2_equivalent_emissions()

        return self.to_dict()

    def make_material_balance(self):
        """Calculate CO2 equivalent emissions for each input row"""
        material_balance = []
        self._total_emissions["materialBalance"] = 0.0
        for row in self.wks_data.get("materialBalance", []):
            gas = row["gas"]
            if not gas:
                material_balance.append(row)
                continue

            gwp = refrigerants_gwp_factors[gas]

            inventory_change = null_replacer(row["inventoryChange"])
            transferred_amount = null_replacer(row["transferredAmount"])
            capacity_change = null_replacer(row["capacityChange"])

            co2_equivalent_emissions = FireSuppression.calculate_co2_emissions_material_balance(
                gwp, inventory_change, transferred_amount, capacity_change
            )

            self._total_emissions["materialBalance"] += co2_equivalent_emissions

            calculated_row = {
                "gas": gas,
                "gasGWP": gwp,
                "inventoryChange": inventory_change,
                "transferredAmount": transferred_amount,
                "capacityChange": capacity_change,
                "CO2EquivalentEmissions": co2_equivalent_emissions,
            }
            material_balance.append(calculated_row)

        self._output["materialBalance"] = material_balance

    def make_simplified_material_balance(self):
        """Calculate CO2 equivalent emissions for each input row"""
        simplified_material_balance = []
        self._total_emissions["simplifiedMaterialBalance"] = 0.0
        for row in self.wks_data.get("simplifiedMaterialBalance", []):
            gas = row["gas"]
            if not gas:
                simplified_material_balance.append(row)
                continue

            gwp = refrigerants_gwp_factors[gas]

            new_units_charge = null_replacer(row["newUnitsCharge"])
            new_units_capacity = null_replacer(row["newUnitsCapacity"])
            existing_units_recharge = null_replacer(row["existingUnitsRecharge"])
            disposed_units_capacity = null_replacer(row["disposedUnitsCapacity"])
            disposed_units_recovered = null_replacer(row["disposedUnitsRecovered"])

            co2_equivalent_emissions = FireSuppression.calculate_co2_emissions_simplified_material_balance(
                gwp,
                new_units_charge,
                new_units_capacity,
                existing_units_recharge,
                disposed_units_capacity,
                disposed_units_recovered,
            )

            self._total_emissions["simplifiedMaterialBalance"] += co2_equivalent_emissions

            calculated_row = {
                "gas": gas,
                "gasGWP": gwp,
                "newUnitsCharge": new_units_charge,
                "newUnitsCapacity": new_units_capacity,
                "existingUnitsRecharge": existing_units_recharge,
                "disposedUnitsCapacity": disposed_units_capacity,
                "disposedUnitsRecovered": disposed_units_recovered,
                "CO2EquivalentEmissions": co2_equivalent_emissions,
            }
            simplified_material_balance.append(calculated_row)

        self._output["simplifiedMaterialBalance"] = simplified_material_balance

    def make_screening_method(self):
        """Calculate CO2 equivalent emissions for each input row"""
        screening_method = []
        self._total_emissions["screeningMethod"] = 0.0
        for row in self.wks_data.get("screeningMethod", []):
            gas_type = row["gasType"]
            type_of_equipment = row["typeOfEquipment"]
            if not gas_type or not type_of_equipment:
                screening_method.append(row)
                continue

            gwp = refrigerants_gwp_factors[gas_type]

            unit_capacity = null_replacer(row["unitsCapacity"])

            co2_equivalent_emissions = FireSuppression.calculate_co2_emissions_screening_method(
                gwp, type_of_equipment, unit_capacity
            )

            self._total_emissions["screeningMethod"] += co2_equivalent_emissions

            calculated_row = {
                "sourceId": row["sourceId"],
                "typeOfEquipment": type_of_equipment,
                "gasType": gas_type,
                "gasGWP": gwp,
                "unitsCapacity": unit_capacity,
                "CO2EquivalentEmissions": co2_equivalent_emissions,
            }
            screening_method.append(calculated_row)

        self._output["screeningMethod"] = screening_method

    @staticmethod
    def calculate_co2_emissions_material_balance(gwp, inventory_change, transferred_amount, capacity_change):
        """Calculate CO2 emissions for a gas given material balance inputs"""
        ret = gwp * (inventory_change + transferred_amount + capacity_change)
        # Handle potential negative values
        ret = max(0.0, ret)
        return ret

    @staticmethod
    # pylint: disable=too-many-arguments
    def calculate_co2_emissions_simplified_material_balance(
        gwp, new_units_charge, new_units_capacity, existing_units_recharge, disposed_units_capacity, disposed_units_recovered
    ):
        """Calculate CO2 emissions for a gas given simplified material balance inputs"""
        ret = gwp * (
            new_units_charge
            - new_units_capacity
            + existing_units_recharge
            + disposed_units_capacity
            - disposed_units_recovered
        )
        # Handle potential negative values
        ret = max(0.0, ret)
        return ret

    @staticmethod
    def calculate_co2_emissions_screening_method(gwp, type_of_equipment, unit_capacity):
        """Calculate CO2 emissions for a gas given simplified material balance inputs"""
        co2_equivalent_emission_factor = fire_suppression_leak_rates_factors[type_of_equipment]

        ret = gwp * co2_equivalent_emission_factor * unit_capacity
        # Handle potential negative values
        ret = max(0.0, ret)
        return ret

    def make_co2_equivalent_emissions(self):
        """Calculate co2 equivalent emissions"""
        total = (
            unit_conversions_factors["pounds"]["kilogram"]
            * (self._total_emissions["materialBalance"] + self._total_emissions["simplifiedMaterialBalance"])
            + self._total_emissions["screeningMethod"]
        ) / 1000.0

        self._output["totalCO2EquivalentEmissions"] = total
