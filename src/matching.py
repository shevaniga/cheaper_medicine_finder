
import json
import pandas as pd
import numpy as np

from cleaning import canonicalize_ingredient


MASS_TO_MG = {
    "mg": 1.0,
    "mcg": 0.001,
    "g": 1000.0
}


def _missing(value):
    if value is None:
        return True

    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _normalise_text(value):
    if _missing(value):
        return None

    return str(value).strip().lower()


def _normalise_number(value):
    if _missing(value):
        return None

    number = float(value)

    if not np.isfinite(number):
        return None

    return round(number, 10)


def _ingredient_signature(item):
  

    if not isinstance(item, dict):
        return None

    if item.get("parse_status") != "parsed":
        return None

    ingredient = canonicalize_ingredient(
        item.get("ingredient")
    )

    if _missing(ingredient):
        return None

    strength_value = _normalise_number(
        item.get("strength_value")
    )

    strength_unit = _normalise_text(
        item.get("strength_unit")
    )

    if strength_value is None or strength_unit is None:
        return None

    
    if strength_unit in MASS_TO_MG:
        strength_value = round(
            strength_value * MASS_TO_MG[strength_unit],
            10
        )
        strength_unit = "mg"

    return {
        "ingredient": str(ingredient),
        "strength_value": strength_value,
        "strength_unit": strength_unit,
        "denominator_value": _normalise_number(
            item.get("denominator_value")
        ),
        "denominator_unit": _normalise_text(
            item.get("denominator_unit")
        ),
        "strength_basis": _normalise_text(
            item.get("strength_basis")
        ),
        "strength_qualifier": _normalise_text(
            item.get("strength_qualifier")
        )
    }



def create_identity_key(parsed_ingredients):
  

    if not isinstance(parsed_ingredients, (list, tuple, np.ndarray)):
        return None

    if len(parsed_ingredients) == 0:
        return None

    signatures = []

    for item in parsed_ingredients:
        signature = _ingredient_signature(item)

        if signature is None:
            return None

        signatures.append(signature)

   
    signatures = sorted(
        signatures,
        key=lambda x: json.dumps(x, sort_keys=True)
    )

    return json.dumps(
        signatures,
        sort_keys=True,
        separators=(",", ":")
    )


def create_matching_groups(df):
   
    result = df.copy()

   
    result["ingredient_identity_key"] = (
        result["parsed_ingredients"].apply(create_identity_key)
    )

   
    result["_form"] = (
        result["dosage_form_normalized"].apply(_normalise_text)
    )

    result["_modifier"] = (
        result["formulation_modifier"].apply(
            lambda x: "unspecified" if _missing(x)
            else _normalise_text(x)
        )
    )

    result["_detail"] = (
        result["formulation_detail"].apply(_normalise_text)
    )

    result["_pack_unit"] = (
        result["pack_unit"].apply(_normalise_text)
    )

   
    def make_match_key(row):

      
        if _missing(row["ingredient_identity_key"]):
            return None

        if _missing(row["_form"]) or row["_form"] == "unknown":
            return None

        if _missing(row["_detail"]):
            return None

        data = [
            row["ingredient_identity_key"],
            row["_form"],
            row["_modifier"],
            row["_detail"]
        ]

        return json.dumps(
            data,
            separators=(",", ":"),
            allow_nan=False
        )

    result["match_group_key"] = result.apply(
        make_match_key,
        axis=1
    )

    def make_price_key(row):

        if _missing(row["match_group_key"]):
            return None

        if _missing(row["_pack_unit"]) or row["_pack_unit"] == "unknown":
            return None

        return json.dumps(
            [
                row["match_group_key"],
                row["_pack_unit"]
            ],
            separators=(",", ":"),
            allow_nan=False
        )

    result["price_group_key"] = result.apply(
        make_price_key,
        axis=1
    )

    return result


def calculate_group_prices(df):

    result = df.copy()

    result["price_per_unit"] = pd.to_numeric(
        result["price_per_unit"],
        errors="coerce"
    )

    result["price"] = pd.to_numeric(
        result["price"],
        errors="coerce"
    )

    result["pack_quantity"] = pd.to_numeric(
        result["pack_quantity"],
        errors="coerce"
    )


    eligible = (
        result["price_group_key"].notna()
        & result["is_discontinued"].eq(False)
        & result["price"].gt(0)
        & result["price_per_unit"].gt(0)
        & result["pack_quantity"].gt(0)
        & result["pack_parse_status"].eq("parsed")
    )

    result["price_eligible"] = eligible

    valid = result.loc[eligible].copy()

    if valid.empty:
        result["group_min_ppu"] = np.nan
        result["group_median_ppu"] = np.nan
        result["group_max_ppu"] = np.nan
        result["group_size"] = 0
        result["savings_per_unit"] = np.nan
        result["savings_percent"] = np.nan
        result["savings_per_pack"] = np.nan

        return result

    stats = (
        valid.groupby("price_group_key")
        .agg(
            group_min_ppu=("price_per_unit", "min"),
            group_median_ppu=("price_per_unit", "median"),
            group_max_ppu=("price_per_unit", "max"),
            group_size=("medicine_id", "count")
        )
        .reset_index()
    )

    result = result.merge(
        stats,
        on="price_group_key",
        how="left"
    )


    result["savings_per_unit"] = (
        result["price_per_unit"] - result["group_min_ppu"]
    )

    result["savings_percent"] = (
        result["savings_per_unit"]
        / result["price_per_unit"]
        * 100
    )

    result["savings_per_pack"] = (
        result["savings_per_unit"] * result["pack_quantity"]
    )


    result.loc[~eligible, [
        "savings_per_unit",
        "savings_percent",
        "savings_per_pack"
    ]] = np.nan

    result["group_size"] = (
        result["group_size"].fillna(0).astype(int)
    )

    return result



def get_alternatives(df, medicine_id, top_n=10):

    selected = df.loc[
        df["medicine_id"] == medicine_id
    ]

    if selected.empty:
        raise ValueError(
            f"Medicine ID {medicine_id} was not found."
        )

    medicine = selected.iloc[0]

    if not medicine["price_eligible"]:
        return pd.DataFrame()

    if medicine["group_size"] < 2:
        return pd.DataFrame()

    alternatives = df.loc[
        df["price_group_key"] == medicine["price_group_key"]
    ].copy()

    alternatives = alternatives.loc[
        alternatives["price_eligible"]
        & (alternatives["medicine_id"] != medicine_id)
    ]

    alternatives["savings_per_unit_vs_selected"] = (
        medicine["price_per_unit"]
        - alternatives["price_per_unit"]
    )

    alternatives["savings_percent_vs_selected"] = (
        alternatives["savings_per_unit_vs_selected"]
        / medicine["price_per_unit"]
        * 100
    )

    alternatives["savings_per_pack_vs_selected"] = (
        alternatives["savings_per_unit_vs_selected"]
        * medicine["pack_quantity"]
    )

    alternatives = alternatives.sort_values(
        "price_per_unit",
        ascending=True
    )

    return alternatives.head(top_n)
