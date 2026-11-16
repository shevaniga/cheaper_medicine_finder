
import re
import pandas as pd


def parse_pack(value):


    if pd.isna(value) or not str(value).strip():
        return {
            "pack_quantity": None,
            "pack_unit": "unknown",
            "pack_container": None,
            "pack_parse_status": "missing"
        }

    text = str(value).strip().lower()

    pattern = (
        r"^\s*(?P<container>.*?)\s+of\s+"
        r"(?P<quantity>\d+(?:\.\d+)?)\s*"
        r"(?P<description>.*?)\s*$"
    )

    match = re.search(pattern, text)

    if not match:
        return {
            "pack_quantity": None,
            "pack_unit": "unknown",
            "pack_container": None,
            "pack_parse_status": "needs_review"
        }

    container = match.group("container").strip()
    quantity = float(match.group("quantity"))
    description = match.group("description").strip()

    unit = "unknown"

  
    # 1. Volume
   

    if re.search(r"\bml\b", description):
        unit = "ml"

    elif re.search(r"\bltr\b|\blitre\b|\bliter\b", description):
        unit = "ml"
        quantity *= 1000

    # 2. Weight
    
    elif re.search(r"\b(gm|grams?|g)\b", description):
        unit = "g"

   
    # 3. International units
   

    elif re.search(r"\biu\b", description):
        unit = "IU"

    # 4. MDI: keep separate, do not assume equivalence
   

    elif re.search(r"\bmdi\b", description):
        unit = "MDI"

    
    # 5. Tablets and similar solid dosage forms
    

    elif re.search(r"\btablets?\b", description):
        unit = "tablet"

    elif re.search(r"\bcapsules?\b", description):
        unit = "capsule"

    elif re.search(r"\btabcaps\b", description):
        unit = "tabcap"

    elif re.search(r"\bcaplets?\b", description):
        unit = "caplet"

    elif re.search(r"\bdisintegrating strips?\b", description):
        unit = "disintegrating_strip"

    elif re.search(r"\blozenges?\b", description):
        unit = "lozenge"

    elif re.search(r"\bpastilles?\b", description):
        unit = "pastille"

    elif re.search(r"\bchewing gums?\b", description):
        unit = "chewing_gum"

   
    # 6. Rectal and vaginal dosage forms
   

    elif re.search(
        r"\b(vaginal suppository|suppositories|suppository)\b",
        description
    ):
        unit = "suppository"

    elif re.search(r"\bpessaries\b", description):
        unit = "pessary"


    # 7. Patches
   

    elif re.search(r"\bpatch(?:es)?\b", description):
        unit = "patch"

   
    # 8. Inhalation products


    elif re.search(r"\brespules\b", description):
        unit = "respule"

    elif re.search(r"\btranspules\b", description):
        unit = "transpule"

    elif re.search(r"\brotacaps\b", description):
        unit = "rotacap"

    elif re.search(r"\brespicaps\b", description):
        unit = "respicap"

    elif re.search(r"\binhalers?\b", description):
        unit = "inhaler"

   
    # 9. Injections
   

    elif re.search(r"\binjections\b", description):
        unit = "injection"

    elif re.search(r"\binjection\b", description):

        if "prefilled syringe" in container:
            unit = "prefilled_syringe"

        elif "pre-filled syringe" in container:
            unit = "prefilled_syringe"

        elif "pen" in container:
            unit = "pen"

        elif "cartridge" in container:
            unit = "cartridge"

        elif "ampoule" in container:
            unit = "ampoule"

        elif "vial" in container:
            unit = "vial"

        else:
            unit = "injection_unit"


    # 10. Other countable products
  

    elif re.search(r"\bsachets?\b", description):
        unit = "sachet"

    elif re.search(r"\bkits?\b", description):
        unit = "kit"

    elif re.search(r"\bsoap\b", description):
        unit = "soap"

    elif re.search(r"\btranscaps\b", description):
        unit = "transcap"

    elif re.search(r"\brespules\b", description):
        unit = "respule"

    elif re.search(r"\bunits?\b", description):
        unit = "unit"

    elif re.search(r"\bpens?\b", description):
        unit = "pen"

    elif re.search(r"\bcartridges?\b", description):
        unit = "cartridge"

    elif re.search(r"\bpouches?\b", description):
        unit = "pouch"

    elif re.search(r"\bbottles?\b", description):
        unit = "bottle"

    elif re.search(r"\bsyrups?\b", description):
        unit = "syrup"

    elif re.search(r"\bsolutions?\b", description):
        unit = "solution"

    
    # 11. Additional validated countable pack formats
   

    if unit == "unknown":

        # Powder for infusion must be checked before general infusion
        if re.search(r"\bpowder for infusion\b", description):
            unit = "powder_infusion_unit"

        elif re.search(r"\binfusions?\b", description):
            unit = "infusion_unit"

        # Proprietary inhalation dosage forms
        elif re.search(r"\bredicaps?\b", description):
            unit = "redicap"

        elif re.search(r"\bnexcaps?\b", description):
            unit = "nexcap"

        elif re.search(r"\boxycaps?\b", description):
            unit = "oxycap"

        elif re.search(r"\brheocaps?\b", description):
            unit = "rheocap"

        elif re.search(r"\binstacaps?\b", description):
            unit = "instacap"

        elif re.search(r"\balicaps?\b", description):
            unit = "alicap"

        elif re.search(r"\bopticops?\b", description):
            unit = "opticop"

        elif re.search(r"\brapitabs?\b", description):
            unit = "rapitab"

        elif re.search(r"\bsoflets?\b", description):
            unit = "soflet"

        # Cartridge spelling variations
        elif re.search(r"\bcartr(?:i|id)ges?\b", description):
            unit = "cartridge"

        # Nasal spray devices
        elif re.search(r"\b(nasal|intranasal)\s+spray\b", description):
            unit = "nasal_spray_device"

        # Eye drops
        elif re.search(r"\beye drops?\b", description):
            unit = "eye_drop_pack"

        # Other countable products
        elif re.search(r"\bgummies\b|\bgummy\b", description):
            unit = "gummy"

        elif re.search(r"\bnebulisers?\b|\bnebulizers?\b", description):
            unit = "nebuliser"

        elif re.search(r"\bdiskettes?\b", description):
            unit = "diskette"

        elif re.search(r"\bampules?\b", description):
            unit = "ampoule"

        elif re.search(r"\bautopen\b", description):
            unit = "autopen"

        elif re.search(r"\bintrauterine system\b", description):
            unit = "intrauterine_system"

        elif re.search(r"\bbandage\b", description):
            unit = "bandage"

        elif re.search(r"\bmouth wash\b", description):
            unit = "mouth_wash"

        elif re.search(r"\bgranules\b", description):
            unit = "granules"

        elif re.search(r"\bpellets\b", description):
            unit = "pellet"

        elif re.search(r"\bfilm\b", description):
            unit = "film"

        elif re.search(r"\bfoam\b", description):
            unit = "foam"

        elif re.search(r"\bpaint\b", description):
            unit = "paint"

        elif re.search(r"\boral liquid\b", description):
            unit = "oral_liquid"

        elif re.search(r"\boral drops\b", description):
            unit = "oral_drops"

        elif re.search(r"\belixirs?\b", description):
            unit = "elixir"

        elif re.search(r"\bshampoos?\b", description):
            unit = "shampoo"

        elif re.search(r"\blotions?\b", description):
            unit = "lotion"

        elif re.search(r"\bgels?\b", description):
            unit = "gel"

        elif re.search(r"\bointments?\b", description):
            unit = "ointment"

        elif re.search(r"\bcreams?\b", description):
            unit = "cream"

        elif re.search(r"\bpowder\b", description):
            unit = "powder"

   
        elif re.search(r"\bprefilled syringes?\b", description):
            unit = "prefilled_syringe"

        elif re.search(r"\bvials?\b", description):
            unit = "vial"

        elif re.search(r"\bcaptabs?\b", description):
            unit = "captab"

        elif re.search(r"\bgums?\b", description):
            unit = "chewing_gum"

        elif re.search(r"\btubes?\b", description):
            unit = "tube_unit"



    if unit == "unknown":
        status = "needs_review"
    else:
        status = "parsed"


    return {
        "pack_quantity": quantity,
        "pack_unit": unit,
        "pack_container": container,
        "pack_parse_status": status
    }


def add_pack_pricing(df):

    result = df.copy()

    parsed_records = [
        parse_pack(value)
        for value in result["pack_size"]
    ]

    parsed_df = pd.DataFrame(
        parsed_records,
        index=result.index
    )

    result = pd.concat(
        [result, parsed_df],
        axis=1
    )

    result["price"] = pd.to_numeric(
        result["price"],
        errors="coerce"
    )

    valid = (
        result["pack_parse_status"].eq("parsed")
        & result["pack_quantity"].gt(0)
        & result["price"].gt(0)
    )

    result["price_per_unit"] = (
        result["price"] / result["pack_quantity"]
    ).where(valid)

    return result
