from typing import Any
from dotenv import load_dotenv
import logging
from dataclasses import dataclass, field
from typing import Annotated, Optional
from pydantic import Field
import time
import yaml
import asyncio
import argparse
import sys
from datetime import datetime, timezone

from livekit import agents, api
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext, metrics, JobContext, JobProcess, UserStateChangedEvent, AgentStateChangedEvent
from livekit.plugins import (
    openai,
    deepgram,
    noise_cancellation,
    silero,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents.voice import MetricsCollectedEvent
import logging

load_dotenv()

logger = logging.getLogger("assistant_dentaire")
logger.setLevel(logging.INFO)

@dataclass
class UserData:
    prenom_client: Optional[str] = None
    nom_client: Optional[str] = None
    telephone_client: Optional[str] = None
    date_heure_rendez_vous: Optional[str] = None
    raison_rendez_vous: Optional[str] = None
    
    agents: dict[str, Agent] = field(default_factory=dict)
    prev_agent: Optional[Agent] = None
    

    def summarize(self) -> str:
        data = {
            "prenom_client": self.prenom_client or "inconnu",
            "nom_client": self.nom_client or "inconnu",
            "telephone_client": self.telephone_client or "inconnu",
            "date_heure_rendez_vous": self.date_heure_rendez_vous or "inconnu",
            "raison_rendez_vous": self.raison_rendez_vous or "inconnu",
        }
        return yaml.dump(data)
    
RunContext_T = RunContext[UserData]

@function_tool()
async def definir_prenom(
    nom: Annotated[str, Field(description="Le prénom du client")],
    context: RunContext_T,
) -> str:
    """Appelé quand le client fournit son prénom."""
    userdata = context.userdata
    userdata.prenom_client = nom
    
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
    userdata.nom_client = nom
    
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
    userdata.telephone_client = telephone
    
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
    userdata.date_heure_rendez_vous = date_heure
    
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
    userdata.raison_rendez_vous = raison
    # Enregistrer la raison du rendez-vous mise à jour
    logger.info(userdata.summarize())
    
    return f"La raison du rendez-vous est mise à jour à {raison}"


class MainAgent(Agent):
    def __init__(self) -> None:
        current_time = datetime.now().strftime('%A %d %B %Y à %H:%M')
        
        HEURES_OUVERTURE = "du lundi au vendredi de 8h00 à 12h00 et de 13h00 à 18h00"
        
        PROMPT_PRINCIPAL = f"""
            Vous êtes l'agent de réservation automatisé de la Clinique Dentaire SmileRight.
            Date et heure actuelles : {current_time}
            {INFO_CLINIQUE}

            POLITIQUE LINGUISTIQUE
            Détectez la première réponse du patient.
            Si elle est en français, menez toute la conversation en français.
            Si elle est en anglais, menez toute la conversation en anglais.
            Ne changez pas de langue une fois la conversation commencée, même si le patient le fait.
            N'utilisez jamais de caractères spéciaux tels que %, $, #, ou *.
            
            RÈGLE NUMÉRO DE TÉLÉPHONE
            Demandez le numéro de téléphone chiffre par chiffre.
            Le format requis est (1) 111 222 3333.
            L'indicatif de pays "(1)" peut être omis par le patient ; s'il manque, ajoutez-le vous-même.
            Toujours épeler ou répéter le numéro chiffre par chiffre.
            Exemple : (1) 5 1 4 5 8 5 9 6 9 1.            
            Cette règle s'applique en français et en anglais.

            PROCESSUS DE RÉSERVATION (ne posez qu'une question à la fois)

            Demandez la date et l'heure de rendez-vous souhaitées.
            Validez que le créneau choisi se situe dans les heures d'ouverture ({HEURES_OUVERTURE}).
            Si ce n'est pas le cas, proposez poliment le créneau disponible le plus proche.

            Demandez le prénom du patient.

            Demandez le nom de famille du patient et demandez qu'il l'épelle lettre par lettre.

            Demandez le numéro de téléphone chiffre par chiffre.

            Demandez la raison de la visite.

            Confirmez tous les détails saisis : date, heure, nom complet, numéro de téléphone et raison.
            Terminez par une remarque de clôture brève telle que :
            – Français : « Nous avons hâte de vous voir ! »
            – Anglais : "We look forward to seeing you!"

            DIRECTIVES GÉNÉRALES
            Ne posez jamais deux questions à la fois.
            Répondez en phrases claires et complètes.
            Si l'utilisateur fournit des informations inattendues, redirigez-le poliment vers l'étape requise.
            Si l'utilisateur demande quelque chose en dehors de votre domaine (par exemple des conseils médicaux), répondez succinctement que vous ne pouvez aider qu'avec la prise de rendez-vous.
            Si l'utilisateur demande des informations générales sur la clinique telles que les heures d'ouverture, l'adresse ou les services disponibles, fournissez les informations demandées dans la langue utilisée pour la conversation."""
            
        logger.info("MainAgent initialisé avec le prompt : %s", PROMPT_PRINCIPAL)
       
        super().__init__(
            instructions=PROMPT_PRINCIPAL,
            tools=[definir_prenom, definir_nom_famille, definir_telephone, definir_date_heure_rendez_vous, definir_raison_rendez_vous, obtenir_date_heure_actuelle, obtenir_info_clinique],
            tts=openai.TTS(voice="nova"),
        )
        
    async def on_enter(self) -> None:
        await self.session.say(
            "Bonjour, bienvenue à la Clinique Dentaire SmileRight, comment puis-je vous aider aujourd'hui ?",
            allow_interruptions=False,
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()
    

async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()
    
    
    userdata = UserData()
    
    userdata.agents.update({
        "agent_principal": MainAgent(),
    })
    
    # Utiliser la classe de session optimisée
    session = AgentSession(
        userdata=userdata,
        stt=deepgram.STT(model="nova-2", language="fr", ),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(voice="nova"),
        vad=silero.VAD.load(),
        turn_detection=MultilingualModel(),
        max_tool_steps=5,
    )
    
    await session.start(
        agent=userdata.agents["agent_principal"],
        room=ctx.room,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

if __name__ == "__main__": 
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))