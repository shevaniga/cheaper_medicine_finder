import re
import pandas as pd

COLUMN_MAPPING = {
    "id": "medicine_id",
    "name": "name",
    "price(₹)": "price",
    "Is_discontinued": "is_discontinued",
    "manufacturer_name": "manufacturer",
    "type": "dosage_form",
    "pack_size_label": "pack_size",
    "short_composition1": "composition1",
    "short_composition2": "composition2",
}

def standardize_columns(df):
    return df.rename(columns=COLUMN_MAPPING).copy()

def clean_text(value):
    if pd.isna(value):
        return pd.NA
    text = str(value)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()

    if text == "":
        return pd.NA
    return text

def clean_price(value):
    if pd.isna(value):
        return float("nan")
    try:
        price = float(value)
    except (ValueError, TypeError):
        return float("nan")
    if price <= 0:
        return float("nan")
    return price


def classify_price(value):
    if pd.isna(value):
        return "missing"
    try:
        price = float(value)
    except (ValueError, TypeError):
        return "non_numeric"
    if price == 0:
        return "zero"
    if price < 0:
        return "negative"
    return "valid"


def prepare_dataset(raw_df):

    df = standardize_columns(raw_df)

    text_columns = [
        "name",
        "manufacturer",
        "dosage_form",
        "pack_size",
        "composition1",
        "composition2",
    ]

    for column in text_columns:
        df[column] = df[column].map(clean_text).astype("string")

    df["price_original"] = df["price"]

    df["price_status"] = df["price_original"].map(classify_price)

    df["price"] = df["price_original"].map(clean_price)

    return df




STRENGTH_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<value>(?:\d+(?:\.\d*)?|\.\d+))
    \s*
    (?P<unit>mcg|µg|ug|mg|gm|g|i\.u\.?|iu|au|units?|u|ml|%)
    \s*
    (?:
        /
        \s*
        (?:(?P<denominator_value>(?:\d+(?:\.\d*)?|\.\d+))\s*)?
        (?P<denominator_unit>mcg|µg|ug|mg|gm|g|ml|spray)
    )?
    \s*
    (?P<basis>w/w|w/v|v/v)?
    \s*$
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

MULTIPLIER_PATTERN = re.compile(
    r"""
    ^\s*
    (?P<value>(?:\d+(?:\.\d*)?|\.\d+))
    \s*
    (?P<unit>million|billion)
    \s*
    (?P<qualifier>.+?)
    \s*$
    """,
    flags=re.IGNORECASE | re.VERBOSE,
)

MILLION_PATTERN = re.compile(
    r"^\s*(?P<value>\d+(?:\.\d+)?)\s*"
    r"million\s*(?P<qualifier>[a-zA-Z].*?)\s*$",
    flags=re.IGNORECASE,
)


def parse_strength(strength_text):
    if pd.isna(strength_text):
        return {
            "strength_value": None,
            "strength_unit": None,
            "denominator_value": None,
            "denominator_unit": None,
            "strength_basis": None,
            "strength_qualifier": None,
            "parse_status": "missing_strength",
        }

    text = str(strength_text).strip()

    if text.upper() in {"NA", "N/A", "NOT AVAILABLE", ""}:
        return {
            "strength_value": None,
            "strength_unit": None,
            "denominator_value": None,
            "denominator_unit": None,
            "strength_basis": None,
            "strength_qualifier": None,
            "parse_status": "missing_strength",
        }

    multiplier_match = MULTIPLIER_PATTERN.fullmatch(text)

    if multiplier_match:
        return {
            "strength_value": float(multiplier_match.group("value")),
            "strength_unit": multiplier_match.group("unit").lower(),
            "denominator_value": None,
            "denominator_unit": None,
            "strength_basis": None,
            "strength_qualifier": clean_text(
                multiplier_match.group("qualifier")
            ),
            "parse_status": "parsed",
        }

    match = STRENGTH_PATTERN.fullmatch(text)

    if not match:
        return {
            "strength_value": None,
            "strength_unit": None,
            "denominator_value": None,
            "denominator_unit": None,
            "strength_basis": None,
            "strength_qualifier": None,
            "parse_status": "unparsed_strength",
        }

    unit = match.group("unit").lower()

    unit_mapping = {
        "u": "units",
        "µg": "mcg",
        "ug": "mcg",
        "gm": "g",
        "iu": "IU",
        "i.u": "IU",
        "i.u.": "IU",
        "au": "AU",
        "unit": "units",
    }

    unit = unit_mapping.get(unit, unit)

    denominator_unit = match.group("denominator_unit")

    if denominator_unit:
        denominator_unit = denominator_unit.lower()
        denominator_unit = unit_mapping.get(
            denominator_unit, denominator_unit
        )

    denominator_value = match.group("denominator_value")

    if denominator_unit and denominator_value is None:
        denominator_value = 1.0

    return {
        "strength_value": float(match.group("value")),
        "strength_unit": unit,
        "denominator_value": (float(denominator_value)
            if denominator_value is not None
            else None
            ),
        "denominator_unit": denominator_unit,
        "strength_basis": (match.group("basis").lower()
            if match.group("basis")
            else None
        ),
        "strength_qualifier": None,
        "parse_status": "parsed",
    }



def parse_ingredient(composition):

    if pd.isna(composition):
        return None

    text = clean_text(composition)

    if pd.isna(text):
        return None

    if "(" not in text or not text.endswith(")"):
        return {
            "raw_composition": text,"ingredient": text,"strength_raw": None,**parse_strength(None),
        }

    ingredient, strength = text.rsplit("(", 1)

    ingredient = clean_text(ingredient)
    strength = strength[:-1].strip()

    strength_data = parse_strength(strength)

    return {
        "raw_composition": text,"ingredient": ingredient, "strength_raw": strength,**strength_data,
    }




def parse_medicine_compositions(row):

    ingredients = []

    for column in ["composition1", "composition2"]:
        parsed = parse_ingredient(row[column])

        if parsed is not None:
            parsed["source_column"] = column
            ingredients.append(parsed)

    return ingredients


def normalize_ingredient_name(value):
    if pd.isna(value):
        return pd.NA

    text = str(value)

    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text).strip()

    text = text.lower()
    return text if text else pd.NA

INGREDIENT_SYNONYMS = {
    "paracetamol/acetaminophen": "paracetamol",
}


def canonicalize_ingredient(value):

    if pd.isna(value):
        return pd.NA

    normalized = normalize_ingredient_name(value)

    return INGREDIENT_SYNONYMS.get(normalized,normalized)


def normalize_strength(row):
    if row["parse_status"] != "parsed":
        return pd.Series({
            "strength_value_normalized": float("nan"),
            "strength_unit_normalized": pd.NA,
            "denominator_value_normalized": float("nan"),
            "denominator_unit_normalized": pd.NA,
            "strength_normalization_status": "not_parsed"
        })

    value = row["strength_value"]
    unit = row["strength_unit"]

    if pd.isna(value) or pd.isna(unit):
        return pd.Series({
            "strength_value_normalized": float("nan"),
            "strength_unit_normalized": pd.NA,
            "denominator_value_normalized": float("nan"),
            "denominator_unit_normalized": pd.NA,
            "strength_normalization_status": "incomplete"
        })

    value = float(value)
    unit = str(unit).strip()


    mass_conversions = {
        "mg": 1.0,
        "mcg": 0.001,
        "g": 1000.0
    }

    unit_lower = unit.lower()

    if unit_lower in mass_conversions:
        normalized_value = value * mass_conversions[unit_lower]
        normalized_unit = "mg"

        if unit_lower == "mg":
            status = "already_mg"
        else:
            status = "converted_to_mg"

    else:
   
        normalized_value = value

        preserved_units = {
            "%": "%",
            "iu": "IU",
            "au": "AU",
            "units": "units",
            "ml": "ml",
            "million": "million",
            "billion": "billion"
        }

        normalized_unit = preserved_units.get(
            unit_lower, unit
        )

        status = "preserved_non_mass"

    denominator_value = row["denominator_value"]
    denominator_unit = row["denominator_unit"]

    if pd.isna(denominator_value):
        denominator_value = float("nan")

    if pd.isna(denominator_unit):
        denominator_unit = pd.NA
    else:
        denominator_unit = str(denominator_unit).strip().lower()

    return pd.Series({
        "strength_value_normalized": normalized_value,
        "strength_unit_normalized": normalized_unit,
        "denominator_value_normalized": denominator_value,
        "denominator_unit_normalized": denominator_unit,
        "strength_normalization_status": status
    })


MASS_TO_MG = {
    "mg": 1.0,
    "mcg": 0.001,
    "g": 1000.0,
}


def normalize_strength_record(row):
    
    result = {
        "strength_value_normalized": float("nan"),
        "strength_unit_normalized": row["strength_unit"],
        "denominator_value_normalized": row["denominator_value"],
        "denominator_unit_normalized": row["denominator_unit"],
        "strength_normalization_status": "not_parsed",
    }

    if row["parse_status"] != "parsed":
        return result

    value = row["strength_value"]
    unit = row["strength_unit"]

    if pd.isna(value) or pd.isna(unit):
        result["strength_normalization_status"] = "incomplete"
        return result

    unit = str(unit).strip().lower()

    if unit in MASS_TO_MG:
        result["strength_value_normalized"] = (
            float(value) * MASS_TO_MG[unit]
        )

        result["strength_unit_normalized"] = "mg"
        result["strength_normalization_status"] = "mass_converted"

    else:
        result["strength_value_normalized"] = float(value)
        result["strength_unit_normalized"] = unit
        result["strength_normalization_status"] = "unchanged_non_mass"

    return result



DOSAGE_FORM_PATTERNS = [
    ("prefilled_syringe", r"\bprefilled\s+syringes?\b"),("inhalation_capsule", r"\b(rotacaps|respicaps)\b"),("nebulizer_unit", r"\brespules?\b"),("vaginal_suppository", r"\bvaginal\s+suppositories\b"),
    ("disintegrating_strip", r"\bdisintegrating\s+strips?\b"),("oral_solution", r"\boral\s+solutions?\b"),("oral_liquid", r"\boral\s+liquids?\b"),("dry_syrup", r"\bdry\s+syrups?\b"),
    ("mouthwash", r"\bmouth\s*wash\b"),("mouth_paint", r"\bmouth\s+paint\b"),("infusion", r"\binfusions?\b"),("expectorant", r"\bexpectorants?\b"),("shampoo", r"\bshampoos?\b"),("toothpaste", r"\btoothpastes?\b"),
    ("lozenge", r"\blozenges?\b"),("granules", r"\bgranules?\b"),("sachet", r"\bsachets?\b"),("gargle", r"\bgargles?\b"),("soap", r"\bsoaps?\b"),("kit", r"\bkits?\b"),("tablet", r"\btablets?\b"),
    ("capsule", r"\bcapsules?\b"),("syrup", r"\bsyrups?\b"),("suspension", r"\bsuspensions?\b"),("injection", r"\binjections?\b"),("inhaler", r"\binhalers?\b"),("drops", r"\bdrops?\b"),("cream", r"\bcreams?\b"),
    ("ointment", r"\bointments?\b"),("gel", r"\bgels?\b"),("powder", r"\bpowders?\b"),("solution", r"\bsolutions?\b"),("spray", r"\bsprays?\b"),("lotion", r"\blotions?\b"),("suppository", r"\bsuppositories\b"),("oral_paste", r"\boral\s+pastes?\b"),
    ("paste", r"\bpastes?\b"),("intrauterine_device", r"\bintrauterine\s+(?:delivery\s+)?systems?\b"r"|\bintrauterine\s+devices?\b"),("dental_varnish", r"\bdental\s+varnishes?\b"),("bio_adhesive", r"\bbio[\s-]?adhesives?\b"),
    ("vaginal_wash", r"\bvaginal\s+wash(?:es)?\b"),("body_wash", r"\bbody\s+wash(?:es)?\b"),("conditioner", r"\bconditioners?\b"),("cleanser", r"\bcleansers?\b"),("enema", r"\benemas?\b"),("emulsion", r"\bemulsions?\b"),
    ("pellets", r"\bpellets?\b"),("aerosol", r"\baerosols?\b"),("tonic", r"\btonics?\b"),("paint", r"\bpaints?\b"),("oil", r"\boils?\b"),("patch", r"\bpatches?\b"),("intrauterine_device",r"\bintrauterine\s+(?:delivery\s+)?systems?\b"r"|\bintrauterine\s+devices?\b"),
    ("dental_varnish", r"\bdental\s+varnishes?\b"),("bio_adhesive", r"\bbio[\s-]?adhesives?\b"),("pellets", r"\bpellets?\b"),("nail_lacquer", r"\bnail\s+lacquer\b"),("oral_emulsion", r"\boral\s+emulsions?\b"),("liniment", r"\bliniments?\b"),
    ("jelly", r"\bjellies\b|\bjelly\b"),("paste", r"\bpastes?\b"),("chewing_gum", r"\bchewing\s+gums?\b"),("pastille", r"\bpastilles?\b"),("patch", r"\bpatches?\b"),("elixir", r"\belixirs?\b"),("face_wash", r"\bface\s+wash\b"),
    ("foam", r"\bfoams?\b"),("bar", r"\bbars?\b"),("husk", r"\bhusk\b"),("serum", r"\bserums?\b"),("vaginal_suppository", r"\bvaginal\s+suppositor(?:y|ies)\b"),("sachet", r"\bsachets?\b"),("nail_lacquer", r"\bnail\s+lacquer\b"),
    ("oral_emulsion", r"\boral\s+emulsions?\b"),("liniment", r"\bliniments?\b"),("jelly", r"\bjell(?:y|ies)\b"),("chewing_gum", r"\bchewing\s+gums?\b"),("pastille", r"\bpastilles?\b"),("patch", r"\bpatches?\b"),("face_wash", r"\bface\s+wash\b"),
    ("serum", r"\bserums?\b"),("foam", r"\bfoams?\b"),("scrub", r"\bscrubs?\b"),("elixir", r"\belixirs?\b"),("ophthalmic_emulsion", r"\bophthalmic\s+emulsions?\b"),("transdermal_patch", r"\btransdermal\s+patch(?:es)?\b"),
    ("vaginal_suppository", r"\bvaginal\s+suppositories?\b"),("oral_paste", r"\boral\s+pastes?\b"),("gum_paint", r"\bgum\s+paint\b"),("inhaler_device", r"\bmdi\b"),("pessary", r"\bpessaries\b|\bpessary\b"),
    ("linctus", r"\blinctus\b"),("liquid", r"\bliquids?\b"),("linctus", r"\blinctus\b"),("transdermal_patch", r"\btransdermal\s+patch(?:es)?\b"),
]



FORMULATION_MODIFIER_PATTERN = re.compile(
    r"\b(sr|er|xr|cr|mr|dr|dt|md)\b",
    flags=re.IGNORECASE
)

MODIFIER_LABELS = {
    "sr": "sustained_release",
    "er": "extended_release_candidate",
    "xr": "extended_release_candidate",
    "cr": "controlled_release_candidate",
    "mr": "modified_release_candidate",
    "dr": "delayed_release_candidate",
    "dt": "dispersible",
    "md": "mouth_dissolving_candidate",
}


def extract_formulation(pack_size):
    """
    Extract dosage form and formulation modifier
    from the original pack-size description.

    Unknown or ambiguous descriptions are preserved.
    """
    if pd.isna(pack_size):
        return {
            "dosage_form_normalized": "unknown",
            "formulation_modifier": pd.NA,
            "formulation_detail": "unknown",
            "formulation_status": "missing_pack_size",
        }

    text = str(pack_size).lower().strip()

    dosage_form = "unknown"

    for form, pattern in DOSAGE_FORM_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            dosage_form = form
            break

    modifier_match = FORMULATION_MODIFIER_PATTERN.search(text)

    modifier = (
        modifier_match.group(1).lower()
        if modifier_match
        else pd.NA
    )

    if pd.notna(modifier):
        detail = MODIFIER_LABELS[modifier]
    else:
        detail = "unspecified"

    status = (
        "identified"
        if dosage_form != "unknown"
        else "unknown_dosage_form"
    )

    return {
        "dosage_form_normalized": dosage_form,
        "formulation_modifier": modifier,
        "formulation_detail": detail,
        "formulation_status": status,
    }


