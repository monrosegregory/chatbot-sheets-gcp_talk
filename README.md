# Chatbot Dialogflow x Google Sheets

Architecture : `Dialogflow ES -> Cloud Run (Python) -> Google Sheets API -> Google Sheet`

## Configuration pour réinstallation rapide
1. **Google Sheets :** Partager le fichier avec l'email du Service Account GCP (accès Éditeur).
2. **GCP Cloud Run :** Déployer la fonction à partir du code dans `/backend`.
3. **Dialogflow ES :** Importer `dialogflow-agent.zip` (Settings > Export and Import > Restore from ZIP) et configurer l'URL dans **Fulfillment**.
