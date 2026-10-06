import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.db import init_db, create_session
from src.data.models import Plano
from src import config

# Quota-based plans configuration
QUOTA_PLANS = {
    "Pacote 10": {"preco": 200.0, "quota_amount": 10},
    "Voucher": {"preco": 0.0, "quota_amount": 0},  # Custom amounts set at purchase
}

def seed_plans():
    print("Initializing database...")
    init_db()  # Ensure table exists
    session = create_session()
    
    print("Migrating plans from config to database...")
    
    try:
        count = 0
        
        # Seed time-based plans from config
        for info_plano in config.PLANOS:
            # Check if exists
            existing = session.query(Plano).filter_by(nome=info_plano).first()
            if existing:
                print(f"Skipping {info_plano} (already exists)")
                continue
                
            preco = config.PLANOS_PRECOS.get(info_plano, 0.0)
            valor_checkin = config.PLANOS_PAGAMENTO_POR_CHECKIN.get(info_plano, 0.0)
            requer_vencimento = info_plano in config.PLANOS_COM_VENCIMENTO
            
            new_plano = Plano(
                nome=info_plano,
                preco=preco,
                valor_por_checkin=valor_checkin,
                requer_vencimento=requer_vencimento,
                ativo=True,
                is_quota=False,
                quota_amount=0
            )
            session.add(new_plano)
            count += 1
            print(f"Adding {info_plano}: Preço={preco}, Checkin={valor_checkin}, Vencimento={requer_vencimento}")
        
        # Seed quota-based plans
        for plan_name, plan_config in QUOTA_PLANS.items():
            existing = session.query(Plano).filter_by(nome=plan_name).first()
            if existing:
                # Update existing plan to be quota-based
                if not existing.is_quota:
                    existing.is_quota = True
                    existing.quota_amount = plan_config["quota_amount"]
                    print(f"Updated {plan_name} to quota-based (quota_amount={plan_config['quota_amount']})")
                else:
                    print(f"Skipping {plan_name} (already exists as quota plan)")
                continue
            
            new_plano = Plano(
                nome=plan_name,
                preco=plan_config["preco"],
                valor_por_checkin=0.0,
                requer_vencimento=False,
                ativo=True,
                is_quota=True,
                quota_amount=plan_config["quota_amount"]
            )
            session.add(new_plano)
            count += 1
            print(f"Adding quota plan {plan_name}: Preço={plan_config['preco']}, Quota={plan_config['quota_amount']}")
            
        session.commit()
        print(f"Migration complete! Added/updated {count} plans.")
        
    except Exception as e:
        session.rollback()
        print(f"Error seeding plans: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_plans()
