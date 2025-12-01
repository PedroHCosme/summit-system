from src.config import PLANOS_PAGAMENTO_POR_CHECKIN, _load_custom_plans_config
from src.data.database_manager import DatabaseManager

print("Config loaded:", PLANOS_PAGAMENTO_POR_CHECKIN)

db = DatabaseManager()
print("Normalized 'Gympass':", db._normalize_plan_for_checkin("Gympass"))
print("Normalized 'Gympass ':", db._normalize_plan_for_checkin("Gympass "))
print("Normalized 'gympass':", db._normalize_plan_for_checkin("gympass"))
