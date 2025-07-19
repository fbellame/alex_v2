from typing import Annotated
from pydantic import Field
from livekit.agents import function_tool, RunContext
from datetime import datetime, timezone
import logging
from shared.user_data import UserData

logger = logging.getLogger("assistant_dentaire")

RunContext_T = RunContext[UserData]

@function_tool()
async def definir_prenom(
    nom: Annotated[str, Field(description="Le prénom du client")],
    context: RunContext_T,
) -> str:
    """Appelé quand le client fournit son prénom."""
    userdata = context.userdata
    userdata.customer_first_name = nom
    
    # Enregistrer le prénom mis à jour
    logger.info(userdata.summarize())
        
    return f"Le prénom est mis à jour à {nom}"

@function_tool()
async def definir_nom_famille(
    nom: Annotated[str, Field(description="Le nom de famille du client")],
    context: RunContext_T,
) -> str:
    """Appelé quand le client fournit son nom de famille."""
    userdata = context.userdata
    userdata.customer_last_name = nom
    
    # Enregistrer le nom de famille mis à jour
    logger.info(userdata.summarize())
        
    return f"Le nom de famille est mis à jour à {nom}"

@function_tool()
async def definir_telephone(
    telephone: Annotated[str, Field(description="Le numéro de téléphone du client")],
    context: RunContext_T,
) -> str:
    """Appelé quand le client fournit son numéro de téléphone."""
    userdata = context.userdata
    userdata.customer_phone = telephone
    
    # Enregistrer le numéro de téléphone mis à jour
    logger.info(userdata.summarize())

    return f"Le numéro de téléphone est mis à jour à {telephone}"

@function_tool()
async def definir_date_heure_rendez_vous(
    date_heure: Annotated[str, Field(description="La date et l'heure du rendez-vous du client")],
    context: RunContext_T
) -> str:
    """Appelé quand le client fournit sa date et heure de rendez-vous."""
    userdata = context.userdata
    logger.info("date_heure: %s", date_heure)
    userdata.booking_date_time = date_heure
    
    # Enregistrer la date et l'heure de rendez-vous mises à jour
    logger.info(userdata.summarize())

    return f"La date et l'heure du rendez-vous sont mises à jour à {date_heure}"

@function_tool()
async def obtenir_date_heure_actuelle(context: RunContext_T) -> str:
    """Obtenir la date et l'heure actuelles."""
    current_time = datetime.now(timezone.utc)
    # Convertir au fuseau horaire de Montréal (EST/EDT)
    montreal_time = current_time.astimezone()
    return f"Date et heure actuelles : {montreal_time.strftime('%A %d %B %Y à %H:%M')}"

# Information constante de la clinique
INFO_CLINIQUE = (
    "La Clinique Dentaire SmileRight est située au 5561 rue St-Denis, Montréal, Canada. "
    "Nos heures d'ouverture sont du lundi au vendredi de 8h00 à 12h00 et de 13h00 à 18h00. "
    "Nous sommes fermés les week-ends."
)

@function_tool()
async def obtenir_info_clinique(context: RunContext_T) -> str:
    """Obtenir les informations sur l'emplacement et les heures d'ouverture de la clinique dentaire."""
    return INFO_CLINIQUE

@function_tool()
async def definir_raison_rendez_vous(
    raison: Annotated[str, Field(description="La raison du rendez-vous")],
    context: RunContext_T
) -> str:
    """Appelé quand l'utilisateur fournit la raison de son rendez-vous."""
    userdata = context.userdata
    userdata.booking_reason = raison
    # Enregistrer la raison du rendez-vous mise à jour
    logger.info(userdata.summarize())
    
    return f"La raison du rendez-vous est mise à jour à {raison}"
