"""Tela de check-in de membros."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QTextBrowser, QFrame
)
from PyQt6.QtCore import Qt

from src.core.plan_status import is_active as plan_is_active


class CheckinScreen(QWidget):
    """Tela de check-in de membros."""
    
    def __init__(self):
        super().__init__()
        self.current_member_id = None
        self._setup_ui()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_label = QLabel("Check-in de Membro")
        title_label.setObjectName("pageTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        subtitle_label = QLabel("Buscar membro → Confirmar dados → Concluir check-in")
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        step_container = QFrame()
        step_container.setStyleSheet(
            "QFrame { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; }"
        )
        step_layout = QHBoxLayout(step_container)
        step_layout.setContentsMargins(8, 4, 8, 4)
        step_layout.setSpacing(10)
        self.step1_label = QLabel("1. Buscar")
        self.step2_label = QLabel("2. Confirmar")
        self.step3_label = QLabel("3. Concluir")
        for step_label in [self.step1_label, self.step2_label, self.step3_label]:
            step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_layout.addWidget(step_label)
        layout.addWidget(step_container)

        self.flow_hint_label = QLabel("Digite o nome do membro e clique em Buscar.")
        self.flow_hint_label.setObjectName("sectionHint")
        self.flow_hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.flow_hint_label)

        search_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Digite o nome do membro para check-in...")
        search_layout.addWidget(self.name_input)

        self.search_button = QPushButton("Buscar")
        self.search_button.setProperty("role", "primary")
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        main_content_layout = QHBoxLayout()

        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_label = QLabel("Resultados da Busca:")
        results_label.setStyleSheet("color: #1a2540; font-weight: bold; font-size: 14px;")
        results_layout.addWidget(results_label)
        
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background-color: #FFFFFF;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 8px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #DDDDDD;
            }
            QListWidget::item:hover {
                background-color: #F0F0F0;
            }
            QListWidget::item:selected {
                background-color: #E67E22;
                color: white;
            }
        """)
        results_layout.addWidget(self.results_list)
        main_content_layout.addWidget(results_container, 1)

        checkin_details_container = QWidget()
        checkin_details_layout = QVBoxLayout(checkin_details_container)
        
        self.member_details_browser = QTextBrowser()
        self.member_details_browser.setHtml("<p style='color: #888888; text-align: center;'>Busque um membro para fazer o check-in.</p>")
        checkin_details_layout.addWidget(self.member_details_browser)

        self.confirm_button = QPushButton("Confirmar Check-in")
        self.confirm_button.setProperty("role", "primary")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setMinimumHeight(50)
        self.confirm_button.setStyleSheet("font-size: 18px; font-weight: bold;")
        checkin_details_layout.addWidget(self.confirm_button)

        self.profile_button = QPushButton("Perfil do Membro")
        self.profile_button.setProperty("role", "secondary")
        self.profile_button.setEnabled(False)
        self.profile_button.setMinimumHeight(40)
        checkin_details_layout.addWidget(self.profile_button)
        
        main_content_layout.addWidget(checkin_details_container, 2)

        layout.addLayout(main_content_layout)
        self._set_step(1)

    def _set_step(self, step: int):
        styles = {
            "active": "background:#E67E22;color:white;border-radius:6px;padding:8px;font-weight:700;",
            "done": "background:#e3fbec;color:#27ae60;border-radius:6px;padding:8px;font-weight:700;",
            "idle": "background:#f8f9fa;color:#718096;border-radius:6px;padding:8px;font-weight:600;",
        }
        labels = [self.step1_label, self.step2_label, self.step3_label]
        for i, label in enumerate(labels, start=1):
            if i < step:
                label.setStyleSheet(styles["done"])
            elif i == step:
                label.setStyleSheet(styles["active"])
            else:
                label.setStyleSheet(styles["idle"])
    
    def set_searching_state(self):
        """Define o estado de busca."""
        self.search_button.setText("Buscando...")
        self.search_button.setEnabled(False)
        self.results_list.clear()
        self.member_details_browser.clear()
        self.confirm_button.setEnabled(False)
        self.profile_button.setEnabled(False)
        self.current_member_id = None
        self._set_step(1)
        self.flow_hint_label.setText("Procurando membro... aguarde.")
    
    def set_ready_state(self):
        """Define o estado pronto."""
        self.search_button.setText("Buscar")
        self.search_button.setEnabled(True)
        if self.results_list.count() == 0:
            self.flow_hint_label.setText("Não encontramos esse membro. Tente nome ou sobrenome.")
    
    def populate_results(self, results: list):
        """Popula a lista de resultados."""
        self.results_list.clear()
        if not results:
            self.member_details_browser.setHtml("<p style='color: #FF6B6B; text-align: center;'>Não encontramos esse membro. Tente nome ou sobrenome.</p>")
            self._set_step(1)
        else:
            self.flow_hint_label.setText("Selecione o membro para confirmar os dados.")
            for result in results:
                nome = result.get('nome', '')
                apelido = result.get('apelido', '')
                display_text = f"{nome} ({apelido})" if apelido else nome
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.ItemDataRole.UserRole, result.get('id'))
                self.results_list.addItem(item)
    
    def display_member_for_checkin(self, member_id: int, member_data: dict):
        """Exibe dados do membro para check-in."""
        self.current_member_id = member_id
        self._set_step(2)
        self.flow_hint_label.setText("Confira os dados e clique em Confirmar Check-in.")
        
        nome = member_data.get('nome')
        apelido = member_data.get('apelido')
        plano = member_data.get('plano')
        estado_plano = member_data.get('estado_plano')
        vencimento_plano = member_data.get('vencimento_plano')
        data_nascimento = member_data.get('data_nascimento')
        whatsapp = member_data.get('whatsapp')
        email = member_data.get('email')
        genero = member_data.get('genero')
        calcado = member_data.get('calcado')
        voucher_credits = member_data.get('voucher_credits', 0) or 0
        
        is_active = plan_is_active(estado_plano)
        color = '#28a745' if is_active else '#FF6B6B'
        
        from src.services.plan_service import get_plan_service
        is_quota_plan = get_plan_service().is_quota_plan(plano)
        
        warning_html = ""
        if not is_active:
            if is_quota_plan:
                pass 
            else:
                warning_html = f"""
                <div style='background-color: #FFF3CD; color: #856404; padding: 10px; 
                            border: 1px solid #FFEEBA; border-radius: 5px; margin-bottom: 15px; text-align: center;'>
                    <strong>⚠️ O plano desse membro está vencido</strong>
                </div>
                """
        
        voucher_warning_html = ""
        if is_quota_plan and voucher_credits <= 0:
            voucher_warning_html = f"""
            <div style='background-color: #F8D7DA; color: #721C24; padding: 10px; 
                        border: 1px solid #F5C6CB; border-radius: 5px; margin-bottom: 15px; text-align: center;'>
                <strong>⚠️ ALERTA: Saldo de vouchers esgotado!</strong><br>
                O check-in será permitido, mas sem cobrança adicional.
            </div>
            """
        
        voucher_section = ""
        if is_quota_plan:
            voucher_color = '#28a745' if voucher_credits > 0 else '#dc3545'
            voucher_section = f"""
            <p><b>Saldo de Vouchers:</b> <span style='color: {voucher_color}; font-weight: bold; font-size: 16px;'>{voucher_credits}</span></p>
            """
            vencimento_plano = None  # Hide vencimento for quota plans

        from src.ui.components.member_info_formatter import format_member_data, calculate_monthly_frequency
        freq = calculate_monthly_frequency(member_id)
        profile_html = format_member_data(member_data, freq)
        
        html = f"<div style='padding: 10px; font-size: 14px;'>{warning_html}{voucher_warning_html}</div>{profile_html}"
        
        self.member_details_browser.setHtml(html)

        self.confirm_button.setEnabled(True)
        self.profile_button.setEnabled(True)
        
        if is_quota_plan and voucher_credits <= 0:
            self.confirm_button.setText("Confirmar Check-in (Sem Saldo!)")
            self.confirm_button.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545; 
                    color: #fff; 
                    font-size: 18px; 
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
        elif not is_active:
            self.confirm_button.setText("Confirmar Check-in (Plano Vencido)")
            self.confirm_button.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107; 
                    color: #000; 
                    font-size: 18px; 
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
        else:
            self.confirm_button.setText("Confirmar Check-in")
            self.confirm_button.setStyleSheet("font-size: 18px; font-weight: bold;")
    
    def show_error(self):
        """Mostra erro ao carregar dados."""
        self.member_details_browser.setHtml("<p style='color: #FF6B6B; text-align: center;'>Erro ao carregar dados do membro.</p>")
        self.confirm_button.setEnabled(False)
        self.profile_button.setEnabled(False)
        self.current_member_id = None
        self._set_step(1)
        self.flow_hint_label.setText("Não foi possível carregar os dados. Tente novamente.")
    
    def clear_after_checkin(self):
        """Limpa a tela após check-in bem-sucedido."""
        self.name_input.clear()
        self.results_list.clear()
        self.member_details_browser.clear()
        self.confirm_button.setEnabled(False)
        self.profile_button.setEnabled(False)
        self.current_member_id = None
        self._set_step(1)
        self.flow_hint_label.setText("Check-in concluído! Você já pode iniciar o próximo.")

    def show_checkin_success_feedback(self, payment_generated: bool = False, payment_amount: float = 0.0):
        """Atualiza a trilha visual para conclusão do fluxo."""
        self._set_step(3)
        if payment_generated:
            self.flow_hint_label.setText(
                f"Check-in concluído. Pagamento de R$ {payment_amount:.2f} registrado."
            )
        else:
            self.flow_hint_label.setText("Check-in concluído com sucesso.")
