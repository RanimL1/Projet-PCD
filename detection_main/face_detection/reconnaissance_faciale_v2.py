"""
=============================================================
  Module de Reconnaissance Faciale — Faculté ENSI
  Outils   : OpenCV + DeepFace (ArcFace) + MySQL
  Version  : multi-photos par étudiant
=============================================================

"""
import cv2
import numpy as np
import mysql.connector
from mysql.connector import Error
from deepface import DeepFace
import os
import json
from datetime import datetime
import bcrypt

# =============================================================
# CONFIGURATION — À MODIFIER SELON TON ENVIRONNEMENT
# =============================================================

DB_CONFIG = {
    "host"    : "localhost",
    "port"    : 3306,
    "user"    : "root",
    "password": "zeineb110803",   # ← ton mot de passe MySQL
    "database": "ecosurveillance"
}

MODELE_FACIAL     = "ArcFace"         # modèle de reconnaissance
BACKEND_DETECTEUR = "opencv"          # détecteur de visages
SEUIL_SIMILARITE  = 0.6               # distance cosinus max (0=identique, 1=différent)

DOSSIER_PHOTOS    = "photos_etudiants"  # dossier contenant les photos
DOSSIER_TEMP      = "temp_faces"        # dossier temporaire (créé automatiquement)
ANGLES_VALIDES = [
    "face",       # face frontale
    "gauche",     # légèrement à gauche
    "droite",     # légèrement à droite
    "pres",       # photo de près (gros plan)
    "loin",       # photo de loin
    "haut",       # angle caméra en hauteur (comme une vraie caméra de surveillance)
    "bas",        # angle caméra en bas
    "masque",     # avec masque (utile pour le campus)
    "lunettes",   # avec lunettes
    "autre"
]

CASCADE_PATH      = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"


# =============================================================
# FONCTION : Parser le nom d'un fichier photo
# =============================================================

def parser_nom_fichier(nom_fichier):
    
    # Supprimer l'extension
    base = os.path.splitext(nom_fichier)[0]

    # Découper par underscore
    parts = base.split("_")

    if len(parts) < 5:
        print(f"[PARSE] ⚠️  Nom invalide : '{nom_fichier}'")
        print(f"         Format attendu : nom_prenom_matricule_filiere_angle.jpg")
        return None

    # Le dernier élément est l'angle
    angle = parts[-1].lower()

    # Vérifier l'angle
    if angle not in ANGLES_VALIDES:
        print(f"[PARSE] ⚠️  Angle invalide '{angle}' dans '{nom_fichier}'")
        print(f"         Angles valides : {', '.join(ANGLES_VALIDES)}")
        return None

    # Les éléments intermédiaires forment : nom, prenom, matricule, filiere
    # On suppose : parts[0]=nom, parts[1]=prenom, parts[2]=matricule, parts[3]=filiere
    # (les éléments supplémentaires avant l'angle sont ignorés)
    nom       = parts[0].capitalize()
    prenom    = parts[1].capitalize()
    matricule = parts[2].upper()
    filiere   = parts[3].capitalize()

    return {
        "nom"      : nom,
        "prenom"   : prenom,
        "matricule": matricule,
        "filiere"  : filiere,
        "angle"    : angle
    }


# =============================================================
# CLASSE : Gestion de la base de données MySQL
# =============================================================

# class BaseDonnees:
#     """
#     Gère toutes les opérations MySQL pour ECO Surveillance.

#     Tables :
#         etudiants       : infos personnelles de l'étudiant
#         photos_etudiants: une ligne par photo, avec embedding ArcFace
#         violations      : chaque incident de littering détecté
#     """

#     def __init__(self):
#         self.connexion = None
#         self._connecter()

#     # ----------------------------------------------------------
#     # Connexion
#     # ----------------------------------------------------------

#     def _connecter(self):
#         try:
#             self.connexion = mysql.connector.connect(**DB_CONFIG)
#             if self.connexion.is_connected():
#                 print("[DB] ✅ Connexion MySQL réussie.")
#         except Error as e:
#             print(f"[DB] ❌ Connexion échouée : {e}")
#             raise

#     def fermer(self):
#         if self.connexion and self.connexion.is_connected():
#             self.connexion.close()
#             print("[DB] Connexion fermée.")

#     # ----------------------------------------------------------
#     # Gestion des étudiants
#     # ----------------------------------------------------------

#     def etudiant_existe(self, matricule):
#         """Vérifie si un étudiant avec cette matricule existe déjà."""
#         cursor = self.connexion.cursor()
#         cursor.execute(
#             "SELECT id FROM etudiants WHERE matricule = %s", (matricule,)
#         )
#         result = cursor.fetchone()
#         cursor.close()
#         return result[0] if result else None

#     def creer_etudiant(self, nom, prenom, matricule, filiere):
#         """
#         Crée un nouvel étudiant dans la table etudiants.
#         Si la matricule existe déjà, retourne l'ID existant.
#         """
#         # Vérifier si déjà présent
#         id_existant = self.etudiant_existe(matricule)
#         if id_existant:
#             return id_existant

#         try:
#             cursor = self.connexion.cursor()
#             cursor.execute("""
#                 INSERT INTO etudiants (nom, prenom, matricule, filiere)
#                 VALUES (%s, %s, %s, %s)
#             """, (nom, prenom, matricule, filiere))
#             self.connexion.commit()
#             etudiant_id = cursor.lastrowid
#             cursor.close()
#             print(f"[DB] 👤 Étudiant créé : {prenom} {nom} ({matricule}) → ID={etudiant_id}")
#             return etudiant_id

#         except Error as e:
#             print(f"[DB] ❌ Erreur création étudiant : {e}")
#             return None

#     # ----------------------------------------------------------
#     # Gestion des photos
#     # ----------------------------------------------------------

#     def photo_existe(self, etudiant_id, angle):
#         """Vérifie si une photo de cet angle existe déjà pour cet étudiant."""
#         cursor = self.connexion.cursor()
#         cursor.execute(
#             "SELECT id FROM photos_etudiants WHERE etudiant_id = %s AND angle = %s",
#             (etudiant_id, angle)
#         )
#         result = cursor.fetchone()
#         cursor.close()
#         return result[0] if result else None

#     def ajouter_photo(self, etudiant_id, photo_path, angle, embedding):
#         """
#         Ajoute une photo et son embedding pour un étudiant.
#         Si une photo du même angle existe déjà, elle est mise à jour.
#         """
#         try:
#             embedding_json = json.dumps(embedding)
#             cursor = self.connexion.cursor()

#             photo_id_existant = self.photo_existe(etudiant_id, angle)

#             if photo_id_existant:
#                 # Mettre à jour
#                 cursor.execute("""
#                     UPDATE photos_etudiants
#                     SET photo_path = %s, embedding = %s, date_ajout = NOW()
#                     WHERE id = %s
#                 """, (photo_path, embedding_json, photo_id_existant))
#                 print(f"[DB]    ↻ Photo '{angle}' mise à jour (ID={photo_id_existant})")
#             else:
#                 # Insérer
#                 cursor.execute("""
#                     INSERT INTO photos_etudiants (etudiant_id, photo_path, angle, embedding)
#                     VALUES (%s, %s, %s, %s)
#                 """, (etudiant_id, photo_path, angle, embedding_json))
#                 print(f"[DB]    ✅ Photo '{angle}' ajoutée")

#             self.connexion.commit()
#             cursor.close()
#             return True

#         except Error as e:
#             print(f"[DB] ❌ Erreur ajout photo : {e}")
#             return False

    # ----------------------------------------------------------
    # Chargement des embeddings pour la reconnaissance
    # ----------------------------------------------------------

    # def charger_tous_embeddings(self):
    #     cursor = self.connexion.cursor(dictionary=True)
    #     cursor.execute("""
    #         SELECT
    #             e.id        AS etudiant_id,
    #             e.nom,
    #             e.prenom,
    #             e.matricule,
    #             e.filiere,
    #             p.id        AS photo_id,
    #             p.angle,
    #             p.embedding
    #         FROM photos_etudiants p
    #         JOIN etudiants e ON p.etudiant_id = e.id
    #         WHERE p.embedding IS NOT NULL
    #         ORDER BY e.id, p.angle
    #     """)
    #     rows = cursor.fetchall()
    #     cursor.close()

    #     # Désérialiser les embeddings JSON
    #     for row in rows:
    #         row["embedding"] = json.loads(row["embedding"])

    #     nb_etudiants = len(set(r["etudiant_id"] for r in rows))
    #     print(f"[DB] 📦 {len(rows)} embeddings chargés pour {nb_etudiants} étudiants.")
    #     return rows

    # # ----------------------------------------------------------
    # # Gestion des violations
    # # ----------------------------------------------------------

    # def enregistrer_violation(self, etudiant_id, track_id, capture_path,
    #                           localisation="Campus ENSI"):
    #     """
    #     Enregistre une violation dans la base.
    #     etudiant_id peut être None si la personne n'est pas identifiée.
    #     """
    #     try:
    #         cursor = self.connexion.cursor()
    #         cursor.execute("""
    #             INSERT INTO violations (etudiant_id, track_id, capture_path, localisation)
    #             VALUES (%s, %s, %s, %s)
    #         """, (etudiant_id, track_id, capture_path, localisation))
    #         self.connexion.commit()
    #         violation_id = cursor.lastrowid
    #         cursor.close()
    #         print(f"[DB] 🚨 Violation #{violation_id} enregistrée "
    #               f"(étudiant_id={etudiant_id}, track_id={track_id})")
    #         return violation_id

    #     except Error as e:
    #         print(f"[DB] ❌ Erreur enregistrement violation : {e}")
    #         return None

    # def get_violations_non_traitees(self):
    #     """Retourne toutes les violations non traitées avec infos étudiant."""
    #     cursor = self.connexion.cursor(dictionary=True)
    #     cursor.execute("""
    #         SELECT
    #             v.id, v.horodatage, v.localisation,
    #             v.capture_path, v.statut, v.track_id,
    #             COALESCE(e.nom,       'Inconnu') AS nom,
    #             COALESCE(e.prenom,    'Inconnu') AS prenom,
    #             COALESCE(e.matricule, '—')       AS matricule,
    #             COALESCE(e.filiere,   '—')       AS filiere
    #         FROM violations v
    #         LEFT JOIN etudiants e ON v.etudiant_id = e.id
    #         WHERE v.statut = 'non_traite'
    #         ORDER BY v.horodatage DESC
    #     """)
    #     results = cursor.fetchall()
    #     cursor.close()
    #     return results

class BaseDonnees:
    """
    Gère toutes les opérations MySQL pour ECO Surveillance.
    Adapté pour la structure Spring Boot (tables: users, detections, infractions, face_vectors)
    """

    def __init__(self):
        self.connexion = None
        self._connecter()

    def _connecter(self):
        try:
            self.connexion = mysql.connector.connect(**DB_CONFIG)
            if self.connexion.is_connected():
                print("[DB] ✅ Connexion MySQL réussie.")
                # Créer les tables si elles n'existent pas
                self._creer_tables_si_necessaire()
        except Error as e:
            print(f"[DB] ❌ Connexion échouée : {e}")
            raise

    def fermer(self):
        if self.connexion and self.connexion.is_connected():
            self.connexion.close()
            print("[DB] Connexion fermée.")

    def _creer_tables_si_necessaire(self):
        """Crée les tables nécessaires si elles n'existent pas"""
        cursor = self.connexion.cursor()
        
        # Table face_vectors si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS face_vectors (
                id INT PRIMARY KEY AUTO_INCREMENT,
                vector TEXT NOT NULL,
                user_id INT UNIQUE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Ajouter la colonne track_id à detections si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE detections ADD COLUMN track_id INT
            """)
        except:
            pass  # La colonne existe déjà
            
        # Ajouter la colonne capture_path à detections si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE detections ADD COLUMN capture_path VARCHAR(255)
            """)
        except:
            pass
            
        # Ajouter la colonne bbox_coordinates à detections si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE detections ADD COLUMN bbox_coordinates TEXT
            """)
        except:
            pass
            
        # Ajouter la colonne detection_id à infractions si elle n'existe pas
        try:
            cursor.execute("""
                ALTER TABLE infractions ADD COLUMN detection_id INT,
                ADD FOREIGN KEY (detection_id) REFERENCES detections(id)
            """)
        except:
            pass
            
        self.connexion.commit()
        cursor.close()

    # ----------------------------------------------------------
    # Gestion des étudiants (table users)
    # ----------------------------------------------------------

    def etudiant_existe(self, matricule):
        """Vérifie si un étudiant avec cette matricule existe déjà dans users."""
        cursor = self.connexion.cursor()
        cursor.execute(
            "SELECT id FROM users WHERE matricule = %s", (matricule,)
        )
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else None

    def creer_etudiant(self, nom, prenom, matricule, filiere):
        """
        Crée un nouvel étudiant dans la table users.
        """
        id_existant = self.etudiant_existe(matricule)
        if id_existant:
            return id_existant

        try:
            cursor = self.connexion.cursor()
            email = f"{prenom.lower()}.{nom.lower()}@ecosurveillance.com"

            mot_de_passe_clair = matricule.lower()  # ex: 24inf001
            mot_de_passe_hashe = bcrypt.hashpw(
                mot_de_passe_clair.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')

            cursor.execute("""
                INSERT INTO users (nom, prenom, email, password, role, matricule)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (nom, prenom, email, mot_de_passe_hashe, "ETUDIANT", matricule))
            self.connexion.commit()
            etudiant_id = cursor.lastrowid
            cursor.close()
            print(f"[DB] 👤 Étudiant créé : {prenom} {nom} ({matricule}) → ID={etudiant_id}")
            return etudiant_id

        except Error as e:
            print(f"[DB] ❌ Erreur création étudiant : {e}")
            return None

    # ----------------------------------------------------------
    # Gestion des vecteurs faciaux (table face_vectors)
    # ----------------------------------------------------------

    def ajouter_vecteur_facial(self, user_id, embedding):
        """
        Ajoute ou met à jour un vecteur facial pour un utilisateur.
        """
        try:
            embedding_json = json.dumps(embedding)
            cursor = self.connexion.cursor()
            
            # Vérifier si un vecteur existe déjà
            cursor.execute(
                "SELECT id FROM face_vectors WHERE user_id = %s", (user_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE face_vectors
                    SET vector = %s
                    WHERE user_id = %s
                """, (embedding_json, user_id))
                print(f"[DB]    ↻ Vecteur facial mis à jour pour user_id={user_id}")
            else:
                cursor.execute("""
                    INSERT INTO face_vectors (user_id, vector)
                    VALUES (%s, %s)
                """, (user_id, embedding_json))
                print(f"[DB]    ✅ Vecteur facial ajouté pour user_id={user_id}")
            
            self.connexion.commit()
            cursor.close()
            return True

        except Error as e:
            print(f"[DB] ❌ Erreur ajout vecteur facial : {e}")
            return False

    # ----------------------------------------------------------
    # Chargement des embeddings pour la reconnaissance
    # ----------------------------------------------------------

    def charger_tous_embeddings(self):
        """
        Charge tous les vecteurs faciaux depuis MySQL.
        """
        cursor = self.connexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                u.id        AS etudiant_id,
                u.nom,
                u.prenom,
                u.matricule,
                fv.vector   AS embedding
            FROM face_vectors fv
            JOIN users u ON fv.user_id = u.id
            WHERE fv.vector IS NOT NULL
        """)
        rows = cursor.fetchall()
        cursor.close()

        for row in rows:
            row["embedding"] = json.loads(row["embedding"])
            row["filiere"] = "Informatique"  # Valeur par défaut

        nb_etudiants = len(set(r["etudiant_id"] for r in rows))
        print(f"[DB] 📦 {len(rows)} vecteurs faciaux chargés pour {nb_etudiants} étudiants.")
        return rows

    # ----------------------------------------------------------
    # Gestion des détections (table detections)
    # ----------------------------------------------------------

    def enregistrer_detection(self, user_id, track_id, capture_path, bbox_coordinates):
        """
        Enregistre une détection dans la table detections.
        """
        try:
            cursor = self.connexion.cursor()
            cursor.execute("""
                INSERT INTO detections (type, detected_at, confirmed, track_id, capture_path, bbox_coordinates, user_id)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s)
            """, ("littering", False, track_id, capture_path, bbox_coordinates, user_id))
            self.connexion.commit()
            detection_id = cursor.lastrowid
            cursor.close()
            print(f"[DB] 🚨 Détection #{detection_id} enregistrée (user_id={user_id}, track_id={track_id})")
            return detection_id

        except Error as e:
            print(f"[DB] ❌ Erreur enregistrement détection : {e}")
            return None

    # ----------------------------------------------------------
    # Créer une infraction automatiquement
    # ----------------------------------------------------------

    def creer_infraction(self, user_id, detection_id, description, preuve_url):
        """
        Crée une infraction liée à une détection.
        """
        try:
            cursor = self.connexion.cursor()
            cursor.execute("""
                INSERT INTO infractions (etudiant_id, description, created_at, infraction_date, status, preuve_url, detection_id)
                VALUES (%s, %s, NOW(), NOW(), %s, %s, %s)
            """, (user_id, description, "EN_ATTENTE", preuve_url, detection_id))
            self.connexion.commit()
            infraction_id = cursor.lastrowid
            cursor.close()
            print(f"[DB] 📝 Infraction #{infraction_id} créée pour détection #{detection_id}")
            return infraction_id

        except Error as e:
            print(f"[DB] ❌ Erreur création infraction : {e}")
            return None


# =============================================================
# CLASSE : Insertion des étudiants depuis un dossier de photos
# =============================================================

class InserteurPhotos:
    """
    Parcourt un dossier de photos, parse les noms de fichiers,
    calcule les embeddings ArcFace et insère tout dans MySQL.

    Format du nom de fichier :
        nom_prenom_matricule_filiere_angle.jpg
    """

    def __init__(self, db: BaseDonnees):
        self.db = db
        os.makedirs(DOSSIER_TEMP, exist_ok=True)

    def calculer_embedding(self, chemin_photo):
        """
        Calcule l'embedding ArcFace d'une photo.
        Retourne la liste de 512 floats ou None en cas d'erreur.
        """
        try:
            resultat = DeepFace.represent(
                img_path         = chemin_photo,
                model_name       = MODELE_FACIAL,
                detector_backend = BACKEND_DETECTEUR,
                enforce_detection= True
            )
            return resultat[0]["embedding"]

        except Exception as e:
            print(f"[EMBED] ❌ Impossible de calculer l'embedding pour '{chemin_photo}' : {e}")
            return None

    def inserer_depuis_dossier(self, dossier=DOSSIER_PHOTOS):
        if not os.path.exists(dossier):
            print(f"[INSERT] ❌ Dossier introuvable : '{dossier}'")
            print(f"          Crée le dossier et place tes photos dedans.")
            return 0

        # Extensions acceptées
        extensions = [".jpg", ".jpeg", ".png"]
        photos = [
            f for f in os.listdir(dossier)
            if os.path.splitext(f)[1].lower() in extensions
        ]

        if not photos:
            print(f"[INSERT] ⚠️  Aucune photo trouvée dans '{dossier}'")
            return 0

        print(f"\n[INSERT] 📂 {len(photos)} photo(s) trouvée(s) dans '{dossier}'")
        print("=" * 60)

        succes   = 0
        echecs   = 0

        for nom_fichier in sorted(photos):
            chemin_complet = os.path.join(dossier, nom_fichier)
            print(f"\n[INSERT] 🖼️  Traitement : {nom_fichier}")

            # 1. Parser le nom du fichier
            infos = parser_nom_fichier(nom_fichier)
            if infos is None:
                echecs += 1
                continue

            # 2. Créer ou récupérer l'étudiant
            etudiant_id = self.db.creer_etudiant(
                nom       = infos["nom"],
                prenom    = infos["prenom"],
                matricule = infos["matricule"],
                filiere   = infos["filiere"]
            )
            if etudiant_id is None:
                echecs += 1
                continue

            # 3. Calculer l'embedding
            print(f"[INSERT]    Calcul de l'embedding ArcFace...")
            embedding = self.calculer_embedding(chemin_complet)
            if embedding is None:
                echecs += 1
                continue

            # 4. Insérer la photo dans la base
            ok = self.db.ajouter_vecteur_facial(
                user_id   = etudiant_id,
                embedding = embedding
            )
            if ok:
                succes += 1
            else:
                echecs += 1

        print("\n" + "=" * 60)
        print(f"[INSERT] ✅ Succès : {succes} photos")
        print(f"[INSERT] ❌ Échecs : {echecs} photos")
        return succes


# =============================================================
# CLASSE : Reconnaissance faciale en temps réel
# =============================================================

class ReconnaissanceFaciale:
    """
    Identifie les visages dans une frame vidéo en 3 étapes :
      1. Haar Cascade (OpenCV) → détection rapide des visages
      2. ArcFace (DeepFace)    → extraction de l'embedding
      3. Distance cosinus      → comparaison avec la base MySQL
    """

    def __init__(self, db: BaseDonnees):
        self.db = db
        self.detecteur_haar = cv2.CascadeClassifier(CASCADE_PATH)
        self.etudiants_db   = self.db.charger_tous_embeddings()
        os.makedirs(DOSSIER_TEMP, exist_ok=True)
        print(f"[FACIAL] ✅ Module initialisé avec {len(self.etudiants_db)} embeddings.")

    def recharger_base(self):
        """Recharge les embeddings depuis MySQL (utile si la base a changé)."""
        self.etudiants_db = self.db.charger_tous_embeddings()
        print(f"[FACIAL] 🔄 Base rechargée : {len(self.etudiants_db)} embeddings.")

    # ----------------------------------------------------------
    # Détection Haar Cascade
    # ----------------------------------------------------------

    def detecter_visages_haar(self, frame):
        """
        Détection rapide des visages avec Haar Cascade.
        Retourne une liste de (x, y, w, h).
        """
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        visages = self.detecteur_haar.detectMultiScale(
            gris,
            scaleFactor  = 1.1,
            minNeighbors = 5,
            minSize      = (60, 60)
        )
        return visages if len(visages) > 0 else []

    # ----------------------------------------------------------
    # Extraction d'embedding ArcFace
    # ----------------------------------------------------------

    def extraire_embedding(self, frame, x, y, w, h):
        """
        Extrait l'embedding ArcFace d'un visage détecté.
        Retourne la liste de 512 floats ou None.
        """
        try:
            # Recadrer le visage avec une marge
            marge = 10
            x1 = max(0, x - marge)
            y1 = max(0, y - marge)
            x2 = min(frame.shape[1], x + w + marge)
            y2 = min(frame.shape[0], y + h + marge)
            visage_crop = frame[y1:y2, x1:x2]

            if visage_crop.size == 0:
                return None

            # Sauvegarder temporairement pour DeepFace
            chemin_temp = os.path.join(DOSSIER_TEMP, "temp_face.jpg")
            cv2.imwrite(chemin_temp, visage_crop)

            # Extraction ArcFace (Haar a déjà localisé le visage)
            resultat = DeepFace.represent(
                img_path         = chemin_temp,
                model_name       = MODELE_FACIAL,
                detector_backend = "skip",
                enforce_detection= False
            )
            return resultat[0]["embedding"]

        except Exception:
            return None

    # ----------------------------------------------------------
    # Distance cosinus
    # ----------------------------------------------------------

    def distance_cosinus(self, emb1, emb2):
        """
        Distance cosinus entre deux embeddings.
        0 = identique, 1 = complètement différent.
        """
        v1 = np.array(emb1)
        v2 = np.array(emb2)
        cosinus = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-10)
        return 1.0 - cosinus

    # ----------------------------------------------------------
    # Identification — meilleure correspondance parmi toutes les photos
    # ----------------------------------------------------------

    def identifier_visage(self, embedding_inconnu):
        """
        Compare l'embedding inconnu avec tous les embeddings de la base.

        Stratégie multi-photos :
            Pour chaque étudiant, on calcule la distance avec CHACUNE
            de ses photos et on garde la PLUS PETITE distance.
            Cela permet de reconnaître la personne même si l'angle
            ne correspond pas exactement à la photo de face.

        Retourne (etudiant_dict, distance) ou (None, distance_min).
        """
        if not self.etudiants_db or embedding_inconnu is None:
            return None, float('inf')

        # Regrouper par etudiant_id, garder la meilleure distance
        meilleurs = {}

        for row in self.etudiants_db:
            eid      = row["etudiant_id"]
            distance = self.distance_cosinus(embedding_inconnu, row["embedding"])

            if eid not in meilleurs or distance < meilleurs[eid]["distance"]:
                meilleurs[eid] = {
                    "distance": distance,
                    "etudiant": row
                }

        if not meilleurs:
            return None, float('inf')

        # Trouver le meilleur étudiant parmi tous
        meilleur = min(meilleurs.values(), key=lambda x: x["distance"])

        if meilleur["distance"] <= SEUIL_SIMILARITE:
            return meilleur["etudiant"], meilleur["distance"]
        else:
            return None, meilleur["distance"]

    # ----------------------------------------------------------
    # Analyse complète d'une frame
    # ----------------------------------------------------------

    def analyser_frame(self, frame):
        """
        Analyse une frame complète :
          1. Détecte tous les visages
          2. Extrait leur embedding
          3. Identifie chaque visage

        Retourne une liste de dicts :
        [{"bbox": (x,y,w,h), "etudiant": dict|None, "distance": float, "identifie": bool}]
        """
        resultats = []
        visages   = self.detecter_visages_haar(frame)

        for (x, y, w, h) in visages:
            embedding          = self.extraire_embedding(frame, x, y, w, h)
            etudiant, distance = self.identifier_visage(embedding)

            resultats.append({
                "bbox"     : (x, y, w, h),
                "etudiant" : etudiant,
                "distance" : distance,
                "identifie": etudiant is not None
            })

        return resultats

    # ----------------------------------------------------------
    # Affichage des résultats sur la frame
    # ----------------------------------------------------------

    def dessiner_resultats(self, frame, resultats):
        """
        Dessine les bounding boxes et labels sur la frame.
        Vert = identifié, Rouge = inconnu.
        """
        for res in resultats:
            x, y, w, h = res["bbox"]
            etudiant    = res["etudiant"]

            if res["identifie"]:
                couleur    = (0, 255, 0)
                label      = f"{etudiant['prenom']} {etudiant['nom']}"
                sous_label = f"{etudiant['matricule']} | {res['distance']:.2f}"  # ✅
            else:
                couleur    = (0, 0, 255)
                label      = "Inconnu"
                sous_label = f"dist={res['distance']:.2f}"

            cv2.rectangle(frame, (x, y), (x + w, y + h), couleur, 2)
            cv2.putText(frame, label,     (x, y - 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, couleur, 2)
            cv2.putText(frame, sous_label,(x, y - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, couleur, 1)

        return frame


# =============================================================
# INTÉGRATION AVEC detection_aoI.py
# =============================================================

# def traiter_alerte_avec_identification(frame, track_id, bbox_person,
#                                        recog: ReconnaissanceFaciale,
#                                        db: BaseDonnees,
#                                        capture_path: str):
#     x1, y1, x2, y2 = [int(v) for v in bbox_person]
#     region = frame[max(0, y1):y2, max(0, x1):x2]

#     if region.size == 0:
#         return None

#     # Analyser les visages dans la région de la personne
#     resultats_visages  = recog.analyser_frame(region)
#     etudiant_identifie = None

#     for res in resultats_visages:
#         if res["identifie"]:
#             etudiant_identifie = res["etudiant"]
#             break

#     # Enregistrer la violation en base
#     etudiant_id  = etudiant_identifie["etudiant_id"] if etudiant_identifie else None
#     violation_id = db.enregistrer_violation(
#         etudiant_id  = etudiant_id,
#         track_id     = track_id,
#         capture_path = capture_path
#     )

#     if etudiant_identifie:
#         print(f"[ALERTE] 🎯 Identifié : {etudiant_identifie['prenom']} "
#               f"{etudiant_identifie['nom']} ({etudiant_identifie['matricule']}) "
#               f"→ Violation #{violation_id}")
#     else:
#         print(f"[ALERTE] ❓ Visage non identifié → Violation #{violation_id} enregistrée.")

#     return {
#         "violation_id"       : violation_id,
#         "track_id"           : track_id,
#         "etudiant"           : etudiant_identifie,
#         "nb_visages_detectes": len(resultats_visages)
#     }

def traiter_alerte_avec_identification(frame, track_id, bbox_person,
                                       recog: ReconnaissanceFaciale,
                                       db: BaseDonnees,
                                       capture_path: str):
    """
    Appelée depuis detection_aoI.py quand un jet de déchet est confirmé.
    """
    import json
    
    x1, y1, x2, y2 = [int(v) for v in bbox_person]
    region = frame[max(0, y1):y2, max(0, x1):x2]
    bbox_json = json.dumps(bbox_person)

    if region.size == 0:
        return None

    # Analyser les visages
    resultats_visages = recog.analyser_frame(region)
    etudiant_identifie = None

    for res in resultats_visages:
        if res["identifie"]:
            etudiant_identifie = res["etudiant"]
            break

    # Enregistrer la détection
    user_id = etudiant_identifie["etudiant_id"] if etudiant_identifie else None
    detection_id = db.enregistrer_detection(
        user_id=user_id,
        track_id=track_id,
        capture_path=capture_path,
        bbox_coordinates=bbox_json
    )

    # Créer une infraction si étudiant identifié
    if user_id and detection_id:
        description = f"Jet de déchet détecté - Track ID: {track_id}"
        db.creer_infraction(user_id, detection_id, description, capture_path)

    if etudiant_identifie:
        print(f"[ALERTE] 🎯 Identifié : {etudiant_identifie['prenom']} "
              f"{etudiant_identifie['nom']} ({etudiant_identifie['matricule']})")
    else:
        print(f"[ALERTE] ❓ Visage non identifié")

    return {
        "detection_id": detection_id,
        "track_id": track_id,
        "etudiant": etudiant_identifie,
        "nb_visages_detectes": len(resultats_visages)
    }
# =============================================================
# POINT D'ENTRÉE — TEST STANDALONE
# =============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("  ECO SURVEILLANCE — Module Reconnaissance Faciale")
    print("=" * 60)

    # 1. Connexion à la base de données
    db = BaseDonnees()

    # 2. Insérer les étudiants depuis le dossier de photos
    #    (à faire une seule fois, ou quand de nouvelles photos sont ajoutées)
    print(f"\n[MAIN] Insertion des photos depuis '{DOSSIER_PHOTOS}'...")
    inserteur = InserteurPhotos(db)
    inserteur.inserer_depuis_dossier(DOSSIER_PHOTOS)

    # 3. Initialiser le module de reconnaissance
    print("\n[MAIN] Initialisation de la reconnaissance faciale...")
    recog = ReconnaissanceFaciale(db)

    # 4. Test en temps réel avec la webcam
    print("\n[MAIN] Ouverture de la webcam...")
    print("[MAIN] Appuie sur 'q' pour quitter, 'r' pour recharger la base.\n")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("[MAIN] ❌ Impossible d'ouvrir la webcam.")
    else:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Analyser et afficher les résultats
            resultats = recog.analyser_frame(frame)
            frame     = recog.dessiner_resultats(frame, resultats)

            # Afficher le nombre de visages détectés
            cv2.putText(frame, f"Visages: {len(resultats)}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow("Reconnaissance Faciale — ECO Surveillance ENSI", frame)

            touche = cv2.waitKey(1) & 0xFF
            if touche == ord('q'):
                break
            elif touche == ord('r'):
                recog.recharger_base()

        cap.release()
        cv2.destroyAllWindows()

    db.fermer()
    print("\n[MAIN] Programme terminé.")