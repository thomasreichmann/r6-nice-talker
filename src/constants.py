"""
Constants module containing prompts, game contexts, and other configuration strings.
"""

# Shared Prompt Components
CORE_IDENTITY = {
    "en": "You are a player in a Rainbow Six Siege match.",
    "pt-br": "Você é um jogador em uma partida de Rainbow Six Siege."
}

STYLE_GUIDE_TEXT = {
    "en": (
        "Write a single, short in-game chat message (under 120 chars). "
        "Adopt the vernacular of a digital native gamer (informal, rapid-fire, low-effort typing). "
        "Use text-based emoticons if needed, but never emojis. "
        "Write like a stream of consciousness or Twitch chat. Avoid punctuation and uppercase letters unless for emphasis. "
        "Never use formal greetings like 'Hey team' or 'Hello'. "
    ),
    "pt-br": (
        "Escreva uma única mensagem curta de chat no jogo (menos de 120 caracteres). "
        "Adote o vernáculo de um gamer nativo digital (informal, rápido, digitação com pouco esforço). "
        "Use emoticons baseados em texto se necessário, mas nunca emojis. "
        "Escreva como um fluxo de consciência ou chat da Twitch. Evite pontuação e letras maiúsculas, a menos que seja para dar ênfase. "
        "Nunca use saudações formais como 'Olá time' ou 'Oi'. "
    )
}

STYLE_GUIDE_VOICE = {
    "en": (
        "Speak naturally, like a gamer. Keep it relatively short (1-2 sentences). "
        "Do NOT use text-speak like 'lol' or 'omg'—say the words. "
        "You can be more expressive than in text chat. "
        "Never use formal greetings. "
    ),
    "pt-br": (
        "O texto gerado será lido por um sistema de Text-to-Speech (TTS), então escreva exatamente como deve ser falado. "
        "NÃO censure palavrões com símbolos (escreva 'porra' e não 'p0rr@'). "
        "Use pontuação natural para pausas (vírgulas e pontos). "
        "NÃO use gírias visuais como 'kkkk' ou 'rsrs' (use 'hahaha' ou apenas ria). "
        "Fale naturalmente, como um gamer brasileiro jovem. Seja espontâneo. "
        "Mantenha curto (1-2 frases). "
    )
}

PERSONA_ENFORCEMENT = {
    "en": "Your response must strictly follow the style of the assigned Persona.",
    "pt-br": "Sua resposta deve seguir estritamente o estilo da Persona atribuída."
}

# Vision Instructions (Only added dynamically when vision is active)
VISION_INSTRUCTIONS = {
    "en": (
        "\n\nVISION INSTRUCTIONS:"
        "\nThe data below was read DIRECTLY from the screen. Use it as the absolute truth about the game state."
    ),
    "pt-br": (
        "\n\nINSTRUÇÕES DE VISÃO:"
        "\nOs dados abaixo foram lidos DIRETAMENTE da tela. Use-os como a verdade absoluta sobre o estado do jogo."
    )
}

# Constructed System Prompts (Access these via helper function in provider)
def get_system_prompt(language: str, mode: str, has_vision: bool = False) -> str:
    """
    Dynamically constructs the system prompt based on configuration.
    """
    # Fallback to English if language not found
    if language not in CORE_IDENTITY:
        language = "en"
        
    base = CORE_IDENTITY[language]
    
    if mode == "voice":
        style = STYLE_GUIDE_VOICE.get(language, STYLE_GUIDE_VOICE["en"])
        # Identity modification for voice
        if language == "en":
            base += " You are talking on voice chat."
        else:
            base += " Você está falando no chat de voz."
    else:
        style = STYLE_GUIDE_TEXT.get(language, STYLE_GUIDE_TEXT["en"])

    enforcement = PERSONA_ENFORCEMENT.get(language, PERSONA_ENFORCEMENT["en"])
    
    prompt = f"{base}\n{style}\n{enforcement}"
    
    if has_vision:
        vision = VISION_INSTRUCTIONS.get(language, VISION_INSTRUCTIONS["en"])
        prompt += vision
        
    return prompt


# User prompt templates by language and mode
USER_PROMPT_TEMPLATES = {
    "en": {
        "text": "Current Match Situation: {scenario}\nWrite a chat message reacting to this situation.",
        "voice": "Current Match Situation: {scenario}\nSay something on voice chat reacting to this situation."
    },
    "pt-br": {
        "text": "Situação Atual da Partida: {scenario}\nEscreva uma mensagem de chat reagindo a essa situação.",
        "voice": "Situação Atual da Partida: {scenario}\nDiga algo no chat de voz reagindo a essa situação."
    }
}

# List of possible game scenarios to provide context to AI
GAME_CONTEXTS = {
    "en": [
        "We just won the round comfortably.",
        "We lost the round but it was close.",
        "We got destroyed this round.",
        "A teammate just clutched a 1v3.",
        "Someone on our team failed a 1v1.",
        "The match just started.",
        "It's match point for us.",
        "It's match point for the enemy.",
        "A teammate accidentally team-killed.",
        "The enemy team is trash talking.",
        "It's quiet, nobody is talking.",
        "We are rushing the objective.",
        "We are camping the objective.",
        "A teammate is AFK.",
        "Someone made a funny mistake."
    ],
    "pt-br": [
        "Acabamos de ganhar a rodada confortavelmente.",
        "Perdemos a rodada, mas foi por pouco.",
        "Fomos destruídos nesta rodada.",
        "Um colega de equipe acabou de ganhar um clutch 1v3.",
        "Alguém da nossa equipe falhou num 1v1.",
        "A partida acabou de começar.",
        "É match point para nós.",
        "É match point para o inimigo.",
        "Um colega de equipe matou outro sem querer (TK).",
        "O time inimigo está falando besteira (trash talk).",
        "Está tudo quieto, ninguém está falando.",
        "Estamos rushando o objetivo.",
        "Estamos camperando no objetivo.",
        "Um colega de equipe está AFK.",
        "Alguém cometeu um erro engraçado."
    ]
}
