class ActionService:
    @staticmethod
    def execute_level_0_action(description: str) -> dict:
        return {
            "level": 0,
            "action": "Normalidad",
            "message": f"Nivel 0 - Normal: {description}. Sin novedades. El área está tranquila."
        }

    @staticmethod
    def execute_level_1_action(description: str) -> dict:
        return {
            "level": 1,
            "action": "Vigilancia Atenta",
            "message": f"Nivel 1 - Vigilancia: {description}. Detectado algo inusual. Monitoreando más de cerca."
        }

    @staticmethod
    def execute_level_2_action(description: str) -> dict:
        return {
            "level": 2,
            "action": "Llamar Serenazgo",
            "message": f"Nivel 2 - Alerta Vecinal: {description}. Situación sospechosa o disturbio menor. Se sugiere presencia de Serenazgo."
        }

    @staticmethod
    def execute_level_3_action(description: str) -> dict:
        return {
            "level": 3,
            "action": "Llamar Policía",
            "message": f"Nivel 3 - Amenaza Confirmada: {description}. Actividad delictiva o agresiva. Se requiere intervención policial."
        }

    @staticmethod
    def execute_level_4_action(description: str) -> dict:
        return {
            "level": 4,
            "action": "Llamar Ambulancia",
            "message": f"Nivel 4 - Emergencia Médica: {description}. Posibles heridos o situación de salud crítica. Solicitar ambulancia."
        }

    @staticmethod
    def execute_level_5_action(description: str) -> dict:
        return {
            "level": 5,
            "action": "PELIGRO INMINENTE / FATAL",
            "message": f"NIVEL 5 - CRÍTICO: {description}. RIESGO DE MUERTE O VIOLENCIA EXTREMA. INTERVENCIÓN TOTAL INMEDIATA."
        }
