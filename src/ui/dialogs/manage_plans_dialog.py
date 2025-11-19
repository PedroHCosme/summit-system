"""Diálogo para gerenciar planos e preços."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QLineEdit, QComboBox,
    QMessageBox, QHeaderView, QDoubleSpinBox, QCheckBox,
    QGroupBox, QTabWidget, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.config import PLANOS_COM_VENCIMENTO  # Mantém apenas esta para verificação inicial


class ManagePlansDialog(QDialog):
    """Diálogo para gerenciar planos e preços."""
    
    plans_updated = pyqtSignal()  # Sinal emitido quando os planos são atualizados
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Gerenciar Planos e Preços")
        self.setMinimumSize(1000, 700)
        self.resize(1100, 750)
        
        # Carregar dados dinamicamente do config para pegar atualizações
        from src import config
        
        # Cópias locais dos dados (editáveis)
        self.planos = config.PLANOS.copy()
        self.planos_precos = config.PLANOS_PRECOS.copy()
        self.planos_pagamento_checkin = config.PLANOS_PAGAMENTO_POR_CHECKIN.copy()
        self.planos_com_vencimento = config.PLANOS_COM_VENCIMENTO.copy()
        
        # Rastrear mudanças
        self.has_changes = False
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Título
        title_label = QLabel("⚙️ Gerenciar Planos e Preços")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Descrição
        desc_label = QLabel(
            "Configure os planos disponíveis, seus preços e regras de negócio.\n"
            "As alterações são salvas localmente e aplicadas imediatamente."
        )
        desc_label.setStyleSheet("color: #666666; font-size: 12px;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #CCCCCC;
                background: #FFFFFF;
                border-radius: 4px;
            }
            QTabBar::tab {
                background: #E0E0E0;
                color: #333333;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #007ACC;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #D0D0D0;
            }
        """)
        
        # Tab 1: Planos e Preços
        plans_tab = self._create_plans_tab()
        self.tabs.addTab(plans_tab, "💳 Planos e Preços")
        
        # Tab 2: Configurações Avançadas
        config_tab = self._create_config_tab()
        self.tabs.addTab(config_tab, "⚙️ Configurações")
        
        layout.addWidget(self.tabs)
        
        # Informação de salvamento
        info_label = QLabel(
            "💡 Dica: As alterações são salvas em um arquivo de configuração local "
            "e não modificam o código-fonte original."
        )
        info_label.setStyleSheet(
            "background-color: #E3F2FD; color: #1976D2; padding: 10px; "
            "border-radius: 4px; font-size: 11px;"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Botões
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.restore_button = QPushButton("🔄 Restaurar Padrões")
        self.restore_button.setFixedHeight(40)
        self.restore_button.clicked.connect(self._restore_defaults)
        self.restore_button.setStyleSheet("""
            QPushButton {
                background-color: #FFA726;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
        """)
        button_layout.addWidget(self.restore_button)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setFixedHeight(40)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                padding: 10px 20px;
            }
        """)
        button_layout.addWidget(self.cancel_button)
        
        self.save_button = QPushButton("💾 Salvar Alterações")
        self.save_button.setFixedHeight(40)
        self.save_button.clicked.connect(self._save_changes)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #28A745;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _create_plans_tab(self):
        """Cria a tab de planos e preços."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Instruções
        instructions = QLabel(
            "Edite os preços dos planos abaixo. Planos com 'Pagamento por Check-in' "
            "cobram no momento do check-in (valor de renovação deve ser 0)."
        )
        instructions.setStyleSheet("color: #555555; font-size: 13px; margin-bottom: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Tabela de planos
        self.plans_table = QTableWidget()
        self.plans_table.setColumnCount(4)
        self.plans_table.setHorizontalHeaderLabels([
            "Plano", "Preço Renovação (R$)", "Pagamento por Check-in (R$)", "Requer Vencimento"
        ])
        
        # Configurar header e colunas
        header = self.plans_table.horizontalHeader()
        if header:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            self.plans_table.setColumnWidth(1, 200)
            self.plans_table.setColumnWidth(2, 230)
            self.plans_table.setColumnWidth(3, 150)
        
        # Configurar altura das linhas
        self.plans_table.verticalHeader().setDefaultSectionSize(50)
        self.plans_table.verticalHeader().setVisible(False)
        
        # Melhorar estilo visual
        self.plans_table.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                gridline-color: #E0E0E0;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 12px 8px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                color: #333333;
                font-weight: bold;
                font-size: 13px;
                padding: 12px 8px;
                border: none;
                border-bottom: 2px solid #007ACC;
            }
        """)
        
        layout.addWidget(self.plans_table)
        
        # Botão para adicionar novo plano
        add_button_layout = QHBoxLayout()
        add_button_layout.addStretch()
        
        self.add_plan_button = QPushButton("➕ Adicionar Novo Plano")
        self.add_plan_button.setFixedHeight(40)
        self.add_plan_button.clicked.connect(self._add_new_plan)
        self.add_plan_button.setStyleSheet("""
            QPushButton {
                background-color: #007ACC;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 4px;
                padding: 8px 20px;
            }
            QPushButton:hover {
                background-color: #005FA3;
            }
        """)
        add_button_layout.addWidget(self.add_plan_button)
        
        layout.addLayout(add_button_layout)
        
        return tab
    
    def _create_config_tab(self):
        """Cria a tab de configurações avançadas."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Grupo: Planos Pay-per-Checkin
        checkin_group = QGroupBox("💳 Planos com Pagamento por Check-in")
        checkin_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #007ACC;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: white;
            }
        """)
        checkin_layout = QVBoxLayout(checkin_group)
        checkin_layout.setSpacing(10)
        
        checkin_info = QLabel(
            "Planos que cobram por check-in em vez de mensalidade fixa.\n"
            "O valor de renovação destes planos deve ser 0."
        )
        checkin_info.setStyleSheet("color: #666666; font-size: 12px; font-weight: normal;")
        checkin_info.setWordWrap(True)
        checkin_layout.addWidget(checkin_info)
        
        self.checkin_plans_label = QLabel()
        self.checkin_plans_label.setStyleSheet(
            "background-color: #F5F5F5; padding: 15px; border-radius: 4px; "
            "font-family: monospace; font-size: 13px; color: #333333; font-weight: normal;"
        )
        self.checkin_plans_label.setWordWrap(True)
        checkin_layout.addWidget(self.checkin_plans_label)
        
        layout.addWidget(checkin_group)
        
        # Grupo: Planos com Vencimento
        vencimento_group = QGroupBox("📅 Planos que Exigem Data de Vencimento")
        vencimento_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #28A745;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: white;
            }
        """)
        vencimento_layout = QVBoxLayout(vencimento_group)
        vencimento_layout.setSpacing(10)
        
        vencimento_info = QLabel(
            "Planos de período fixo que requerem controle de vencimento.\n"
            "Planos pay-per-checkin geralmente não precisam de vencimento."
        )
        vencimento_info.setStyleSheet("color: #666666; font-size: 12px; font-weight: normal;")
        vencimento_info.setWordWrap(True)
        vencimento_layout.addWidget(vencimento_info)
        
        self.vencimento_plans_label = QLabel()
        self.vencimento_plans_label.setStyleSheet(
            "background-color: #F5F5F5; padding: 15px; border-radius: 4px; "
            "font-family: monospace; font-size: 13px; color: #333333; font-weight: normal;"
        )
        self.vencimento_plans_label.setWordWrap(True)
        vencimento_layout.addWidget(self.vencimento_plans_label)
        
        layout.addWidget(vencimento_group)
        
        # Grupo: Futuras Configurações (Placeholder)
        future_group = QGroupBox("🔮 Configurações Futuras")
        future_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #CCCCCC;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: white;
            }
        """)
        future_layout = QVBoxLayout(future_group)
        
        future_info = QLabel(
            "Em breve:\n"
            "• Grace Period (dias de tolerância após vencimento)\n"
            "• Pro-rata (cálculo proporcional de valores)\n"
            "• Descontos automáticos (família, trimestral, etc.)\n"
            "• Regras de upgrade/downgrade de planos"
        )
        future_info.setStyleSheet("color: #999999; font-size: 12px; font-style: italic; font-weight: normal;")
        future_layout.addWidget(future_info)
        
        layout.addWidget(future_group)
        
        layout.addStretch()
        
        return tab
    
    def _load_data(self):
        """Carrega os dados na tabela."""
        self.plans_table.setRowCount(len(self.planos))
        
        for row, plano in enumerate(self.planos):
            # Definir altura da linha
            self.plans_table.setRowHeight(row, 50)
            
            # Coluna 0: Nome do plano
            name_item = QTableWidgetItem(plano)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            name_item.setBackground(Qt.GlobalColor.lightGray)
            font = QFont()
            font.setPointSize(12)
            font.setBold(True)
            name_item.setFont(font)
            self.plans_table.setItem(row, 0, name_item)
            
            # Coluna 1: Preço de renovação
            price_spin = QDoubleSpinBox()
            price_spin.setRange(0, 10000)
            price_spin.setSingleStep(10)
            price_spin.setDecimals(2)
            price_spin.setPrefix("R$ ")
            price_spin.setValue(self.planos_precos.get(plano, 0))
            price_spin.setMinimumHeight(40)
            price_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
            price_spin.setStyleSheet("""
                QDoubleSpinBox {
                    font-size: 14px;
                    padding: 8px 35px 8px 8px;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }
                QDoubleSpinBox::up-button {
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 30px;
                    height: 19px;
                    border-left: 1px solid #CCCCCC;
                    border-bottom: 1px solid #CCCCCC;
                    background-color: #F5F5F5;
                }
                QDoubleSpinBox::up-button:hover {
                    background-color: #E0E0E0;
                }
                QDoubleSpinBox::up-arrow {
                    image: none;
                    width: 0px;
                    height: 0px;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-bottom: 8px solid #333333;
                }
                QDoubleSpinBox::down-button {
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 30px;
                    height: 19px;
                    border-left: 1px solid #CCCCCC;
                    background-color: #F5F5F5;
                }
                QDoubleSpinBox::down-button:hover {
                    background-color: #E0E0E0;
                }
                QDoubleSpinBox::down-arrow {
                    image: none;
                    width: 0px;
                    height: 0px;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 8px solid #333333;
                }
            """)
            price_spin.valueChanged.connect(self._mark_as_changed)
            self.plans_table.setCellWidget(row, 1, price_spin)
            
            # Coluna 2: Pagamento por check-in
            checkin_spin = QDoubleSpinBox()
            checkin_spin.setRange(0, 1000)
            checkin_spin.setSingleStep(5)
            checkin_spin.setDecimals(2)
            checkin_spin.setPrefix("R$ ")
            checkin_spin.setValue(self.planos_pagamento_checkin.get(plano, 0))
            checkin_spin.setMinimumHeight(40)
            checkin_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
            checkin_spin.setStyleSheet("""
                QDoubleSpinBox {
                    font-size: 14px;
                    padding: 8px 35px 8px 8px;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }
                QDoubleSpinBox::up-button {
                    subcontrol-origin: border;
                    subcontrol-position: top right;
                    width: 30px;
                    height: 19px;
                    border-left: 1px solid #CCCCCC;
                    border-bottom: 1px solid #CCCCCC;
                    background-color: #F5F5F5;
                }
                QDoubleSpinBox::up-button:hover {
                    background-color: #E0E0E0;
                }
                QDoubleSpinBox::up-arrow {
                    image: none;
                    width: 0px;
                    height: 0px;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-bottom: 8px solid #333333;
                }
                QDoubleSpinBox::down-button {
                    subcontrol-origin: border;
                    subcontrol-position: bottom right;
                    width: 30px;
                    height: 19px;
                    border-left: 1px solid #CCCCCC;
                    background-color: #F5F5F5;
                }
                QDoubleSpinBox::down-button:hover {
                    background-color: #E0E0E0;
                }
                QDoubleSpinBox::down-arrow {
                    image: none;
                    width: 0px;
                    height: 0px;
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 8px solid #333333;
                }
            """)
            checkin_spin.valueChanged.connect(self._mark_as_changed)
            self.plans_table.setCellWidget(row, 2, checkin_spin)
            
            # Coluna 3: Requer vencimento
            vencimento_check = QCheckBox()
            vencimento_check.setChecked(plano in self.planos_com_vencimento)
            vencimento_check.setStyleSheet("""
                QCheckBox::indicator {
                    width: 24px;
                    height: 24px;
                }
            """)
            vencimento_check.stateChanged.connect(self._mark_as_changed)
            
            # Centralizar checkbox
            check_widget = QWidget()
            check_layout = QHBoxLayout(check_widget)
            check_layout.addWidget(vencimento_check)
            check_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            check_layout.setContentsMargins(0, 0, 0, 0)
            self.plans_table.setCellWidget(row, 3, check_widget)
        
        # Atualizar labels da tab de configurações
        self._update_config_labels()
    
    def _update_config_labels(self):
        """Atualiza os labels de configuração."""
        # Planos pay-per-checkin
        checkin_plans = [p for p in self.planos if self.planos_pagamento_checkin.get(p, 0) > 0]
        if checkin_plans:
            checkin_text = "\n".join([
                f"• {p}: R$ {self.planos_pagamento_checkin[p]:.2f} por check-in"
                for p in checkin_plans
            ])
        else:
            checkin_text = "Nenhum plano configurado"
        self.checkin_plans_label.setText(checkin_text)
        
        # Planos com vencimento
        if self.planos_com_vencimento:
            vencimento_text = "\n".join([f"• {p}" for p in self.planos_com_vencimento])
        else:
            vencimento_text = "Nenhum plano configurado"
        self.vencimento_plans_label.setText(vencimento_text)
    
    def _mark_as_changed(self):
        """Marca que houve alterações."""
        self.has_changes = True
    
    def _add_new_plan(self):
        """Adiciona um novo plano."""
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(
            self,
            "Novo Plano",
            "Digite o nome do novo plano:",
            QLineEdit.EchoMode.Normal
        )
        
        if ok and name.strip():
            name = name.strip()
            
            # Verificar se já existe
            if name in self.planos:
                QMessageBox.warning(
                    self,
                    "Plano Existente",
                    f"O plano '{name}' já existe!"
                )
                return
            
            # Adicionar às listas
            self.planos.append(name)
            self.planos_precos[name] = 0.0
            self.planos_pagamento_checkin[name] = 0.0
            
            # Recarregar tabela
            self._load_data()
            self._mark_as_changed()
            
            QMessageBox.information(
                self,
                "Plano Adicionado",
                f"Plano '{name}' adicionado com sucesso!\n\n"
                f"Configure o preço e as opções na tabela."
            )
    
    def _restore_defaults(self):
        """Restaura os valores padrões."""
        reply = QMessageBox.question(
            self,
            "Restaurar Padrões",
            "Deseja restaurar todos os planos e preços para os valores padrão?\n\n"
            "Esta ação não pode ser desfeita!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Recarregar valores originais
            from src import config
            import importlib
            importlib.reload(config)
            
            self.planos = config.PLANOS.copy()
            self.planos_precos = config.PLANOS_PRECOS.copy()
            self.planos_pagamento_checkin = config.PLANOS_PAGAMENTO_POR_CHECKIN.copy()
            self.planos_com_vencimento = config.PLANOS_COM_VENCIMENTO.copy()
            
            # Recarregar interface
            self._load_data()
            self._mark_as_changed()
            
            QMessageBox.information(
                self,
                "Padrões Restaurados",
                "Os valores padrão foram restaurados.\n\n"
                "Clique em 'Salvar Alterações' para aplicar."
            )
    
    def _save_changes(self):
        """Salva as alterações."""
        try:
            # Coletar dados da tabela
            self.planos_precos = {}
            self.planos_pagamento_checkin = {}
            self.planos_com_vencimento = []
            
            for row in range(self.plans_table.rowCount()):
                plano = self.plans_table.item(row, 0).text()
                
                # Preço de renovação
                price_spin = self.plans_table.cellWidget(row, 1)
                if price_spin:
                    self.planos_precos[plano] = price_spin.value()
                
                # Pagamento por check-in
                checkin_spin = self.plans_table.cellWidget(row, 2)
                if checkin_spin:
                    value = checkin_spin.value()
                    if value > 0:
                        self.planos_pagamento_checkin[plano] = value
                
                # Requer vencimento
                check_widget = self.plans_table.cellWidget(row, 3)
                if check_widget:
                    checkbox = check_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        self.planos_com_vencimento.append(plano)
            
            # Salvar em arquivo
            self._save_to_file()
            
            QMessageBox.information(
                self,
                "Salvo com Sucesso",
                "As configurações foram salvas com sucesso!\n\n"
                "As alterações já estão ativas no sistema."
            )
            
            self.has_changes = False
            self.plans_updated.emit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro ao Salvar",
                f"Erro ao salvar configurações:\n\n{str(e)}"
            )
    
    def _save_to_file(self):
        """Salva as configurações em arquivo."""
        import json
        import os
        from pathlib import Path
        
        # Caminho do arquivo de configuração (raiz do projeto)
        # __file__ = .../src/ui/dialogs/manage_plans_dialog.py
        # .parent.parent.parent.parent = raiz do projeto
        project_root = Path(__file__).parent.parent.parent.parent
        config_file = project_root / "plans_config.json"
        
        # Preparar dados
        config_data = {
            "PLANOS": self.planos,
            "PLANOS_PRECOS": self.planos_precos,
            "PLANOS_PAGAMENTO_POR_CHECKIN": self.planos_pagamento_checkin,
            "PLANOS_COM_VENCIMENTO": self.planos_com_vencimento,
            "_metadata": {
                "version": "1.0",
                "last_updated": str(__import__('datetime').datetime.now()),
                "description": "Configuração de planos e preços editada via UI"
            }
        }
        
        # Salvar JSON
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        # Atualizar config.py em memória (para aplicar imediatamente)
        from src import config
        config.PLANOS = self.planos.copy()
        config.PLANOS_PRECOS = self.planos_precos.copy()
        config.PLANOS_PAGAMENTO_POR_CHECKIN = self.planos_pagamento_checkin.copy()
        config.PLANOS_COM_VENCIMENTO = self.planos_com_vencimento.copy()
    
    def closeEvent(self, event):
        """Intercepta o fechamento para confirmar se há mudanças."""
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Alterações Não Salvas",
                "Você tem alterações não salvas.\n\n"
                "Deseja salvá-las antes de sair?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._save_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
