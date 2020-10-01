# Part 0 -- INFO

# Part 1 -- Imports
import os

import pandas as pd

pd.options.mode.chained_assignment = None
report_path = "output"
if not os.path.exists(report_path):
    os.makedirs(report_path)

# Part 2 -- Directory location
# --> Uncomment the following lines to manually input the directory and file.
# filename will need to be changed once you receive the new file.
# filename = "2020-02-27_alertes_except_dechet_v2.xlsx"
# path = "../Data/" + filename

file = [f.name for f in os.scandir("../Data") if f.is_file()]
path = "../Data/" + file[0]
print(f"Lecture et analyse du fichier : {path}")
df = pd.read_excel(path)


# Part 3 -- Initial filter
df_transfusion = df[(df["type"] == "transfusion") & (df["statut"] == "activé")]

# Part 4 -- Formatting
df_transfusion["al1_6"] = pd.to_datetime(df_transfusion["al1_6"], format="%Y-%m-%d")

# Part 5 -- Second filter, files to verify
df_transfusion_null = df_transfusion[df_transfusion["nte_3"] == "(null)"]
df_transfusion = df_transfusion[df_transfusion["nte_3"] != "(null)"]

# Part 6 -- Formatting
df_transfusion_br = df_transfusion[df_transfusion["nte_3"].str.contains(r"\\.br\\")]
df_transfusion["nte_3"] = df_transfusion["nte_3"].str.replace(r"\\.br\\", " ; ")

# Part 7 -- Formatting
df_transfusion["nte_3"] = df_transfusion["nte_3"].replace(
    {"[aA]nti[-\s]": "Anti-"}, regex=True
)

# Part 8 -- Filtering
to_transfer = [
    "Ac antiérythrocytaires",
    "Greffe de cellules souches",
    "Changement de groupe",
    "Agglutinines froides",
    "Blocage transfusionnel",
]

# Part 9 -- Filtering (from part 8)
dict = {}
for value in to_transfer:
    dict["df_transfusion_{0}".format(value.replace(" ", "_"))] = df_transfusion[
        df_transfusion["al1_3"] == value
    ]

# Part 10 -- Drop duplicate, Filtering
for key, value in dict.items():
    # result_df = value.apply(lambda x: x.astype(str).str.lower()).drop_duplicates(
    #     subset=["numpat", "nte_3", "al1_6", "statut"]
    # )
    # value = value.loc[result_df.index]
    # Create a new column with the lenght of the strings. This is used in the case
    # where there are 2 different alerts on the same day, we want to retrieve the most
    # complete.
    value["length"] = value["nte_3"].apply(lambda x: len(x))
    value.drop_duplicates(["numpat", "nte_3", "al1_6"], inplace=True)
    # value.drop_duplicates(["numpat","nte_3", "al1_6","statut"], inplace=True)
    value.sort_values(
        ["numpat", "al1_6", "length"], ascending=[True, False, False], inplace=True
    )
    value.drop_duplicates(["numpat", "nte_3"], inplace=True, keep="last")

# Part 11 -- Try to aggregate and filter out duplicate. NOT VALIDATED !
dict_grouped_test = {}
for key, value in dict.items():
    dict_grouped_test["grouped_{0}".format(key)] = (
        dict[key]
        .groupby("numpat")["nte_3"]
        .apply(", ".join)
        .reset_index(name="test_aggregate")
    )
    # dict_grouped_test["grouped_{0}".format(key)] = (
    #     dict[key]
    #     .groupby("numpat")["nte_3"]
    #     .apply(list)
    #     .reset_index(name="test_aggregate")
    # )

# Part 12 -- Aggregate filtering. NOT VALIDATED !
for key, value in dict_grouped_test.items():
    value["test"] = value["test_aggregate"].str.findall(
        r"((?:auto[ -])?[Aa]nti-[\s]*\S[^,. :;]*)"
    )  # (Anti-[\s]*\S[^,. :;]*)#(r"(Anti-\S[^, .:]*)")
    value["test_2"] = value["test"].apply(set)
# Last regex : (Anti-\s*\S[^,. :]*)+?(?=Anti)*

# Part 13 -- Export format definition + aggregation. VALIDATED
def f(x):
    d = {}
    d["id_pat"] = x["pid_3"].iloc[0]
    d["date_summary"] = x["al1_6"].iloc[0]
    d["note_summary"] = x["nte_3"].iloc[0]
    d["type"] = max(x["al1_3"], key=len)
    d["note_text"] = "; ".join((x["al1_6"].astype(str) + " : " + x["nte_3"]).tolist())
    return pd.Series(d, index=["type", "date_summary", "note_summary", "note_text"])


# Part 14 -- Apply previous step.
dict_grouped = {}
for key, value in dict.items():
    # grouped = dict[key].groupby("numpat")
    dict_grouped["grouped_{0}".format(key)] = (
        dict[key].groupby("numpat").apply(f).reset_index()
    )

# Part 15 -- Adding the aggregate to the export format. NOT VALIDATED.
dict_grouped["grouped_df_transfusion_Ac_antiérythrocytaires"][
    "aggregate (non validé)"
] = dict_grouped_test["grouped_df_transfusion_Ac_antiérythrocytaires"]["test_aggregate"]
dict_grouped["grouped_df_transfusion_Ac_antiérythrocytaires"][
    "test (non validé)"
] = dict_grouped_test["grouped_df_transfusion_Ac_antiérythrocytaires"]["test"]
dict_grouped["grouped_df_transfusion_Ac_antiérythrocytaires"][
    "test_dict (non validé)"
] = dict_grouped_test["grouped_df_transfusion_Ac_antiérythrocytaires"]["test_2"]

# Part 16 -- Export.
with pd.ExcelWriter(
    os.path.join(report_path, "import_alert_transf" + ".xlsx")
) as writer:
    for key in dict_grouped:
        # Par catégorie d'alerte, toutes les alertes regroupées de façon à n'avoir
        # qu'une ligne par patient.
        dict_grouped[key].to_excel(writer, sheet_name=key[:30])
    for key in dict:
        # Par catégorie d'alerte, toutes les alertes nettoyées et filtrées.
        dict[key].to_excel(writer, sheet_name=key[:30])

    # Toutes les alertes telles que reçues initialement.
    df_transfusion.to_excel(writer, sheet_name="df_transfusion")

    # Toutes les alertes pour lesquelles la valeur (null) était référencée.
    df_transfusion_null.to_excel(writer, sheet_name="df_transfusion_null")

    # Toutes les alertes pour lesquelles le caractère \.br\ a été remplacé.
    df_transfusion_br.to_excel(writer, sheet_name="df_transfusion_br")

print(
    'Attention, les colonnes "aggregate", "test" et "test_2" n\'ont jamais été '
    "validées."
)
print(
    "Les données de ces colonnes ont été manipulées et modifiées et sont susceptibles "
    "d'être incorrectes."
)
print(
    "Ces colonnes n'ont pour vocation que de permettre détecter les patients n'ayant "
    "qu'un seul type d'anticorps, que l'on pourrait qualifier de \"bénin\""
)
