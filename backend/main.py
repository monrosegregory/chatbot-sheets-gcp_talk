import json
import re
import functions_framework
import gspread
from google.cloud import secretmanager
from google.oauth2.service_account import Credentials

PROJECT_ID = "chatbot-spreadheet"
SECRET_ID = "gsheet-credentials"


def get_service_account_from_secret_manager():
  client = secretmanager.SecretManagerServiceClient()
  name = f"projects/{PROJECT_ID}/secrets/{SECRET_ID}/versions/latest"
  response = client.access_secret_version(request={"name": name})
  return json.loads(response.payload.data.decode("UTF-8"))


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


@functions_framework.http
def hello_http(request):
  if request.method == "OPTIONS":
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "3600",
    }
    return ("", 204, headers)

  headers = {
      "Access-Control-Allow-Origin": "*",
      "Content-Type": "application/json",
  }

  try:
    request_json = request.get_json(silent=True) or {}

    texte_recu = ""
    if "prompt" in request_json:
      texte_recu = str(request_json["prompt"])
    elif (
        "queryResult" in request_json
        and "queryText" in request_json["queryResult"]
    ):
      texte_recu = request_json["queryResult"]["queryText"]
    else:
      for key in ["message", "text", "commande", "query"]:
        if key in request_json and request_json[key]:
          texte_recu = str(request_json[key])
          break

    if not texte_recu and request_json:
      texte_recu = str(list(request_json.values())[0])

    parameters = request_json.get("queryResult", {}).get("parameters", {})
    num_recherche = str(
        parameters.get("commande") or parameters.get("number") or ""
    )

    if not num_recherche:
      numeros = re.findall(r"\d+", texte_recu)
      num_recherche = numeros[0] if numeros else texte_recu.strip()

    service_account_info = get_service_account_from_secret_manager()
    creds = Credentials.from_service_account_info(
        service_account_info, scopes=SCOPES
    )
    gc = gspread.authorize(creds)

    sheet = gc.open("Commandes_2026").sheet1
    lignes = sheet.get_all_values()

    statut_trouve = None
    client_nom = None
    date_livraison = None

    num_recherche_clean = re.sub(r"\D", "", str(num_recherche))

    for idx, ligne in enumerate(lignes[1:], start=2):
      if not ligne or not ligne[0]:
        continue

      val_cellule = str(ligne[0]).strip()
      val_cellule_clean = re.sub(r"\D", "", val_cellule)

      if (num_recherche_clean and val_cellule_clean == num_recherche_clean) or (
          val_cellule.lower() == str(num_recherche).strip().lower()
      ):
        client_nom = ligne[1] if len(ligne) > 1 else "Inconnu"
        statut_trouve = ligne[2] if len(ligne) > 2 else "Non précisé"
        date_livraison = ligne[3] if len(ligne) > 3 else "N/A"
        break

    if statut_trouve:
      response_payload = {
          "trouve": True,
          "commande_id": str(num_recherche),
          "client": client_nom,
          "statut": statut_trouve,
          "date_livraison": date_livraison,
          "fulfillmentText": (
              f"La commande {num_recherche} de {client_nom} est :"
              f" {statut_trouve}."
          ),
      }
    else:
      response_payload = {
          "trouve": False,
          "commande_id": str(num_recherche),
          "erreur": f"Commande {num_recherche} non trouvée dans le fichier.",
          "fulfillmentText": f"Commande {num_recherche} introuvable.",
      }

    return (json.dumps(response_payload), 200, headers)

  except Exception as e:
    err_payload = {"trouve": False, "erreur": f"Erreur serveur : {str(e)}"}
    return (json.dumps(err_payload), 500, headers)