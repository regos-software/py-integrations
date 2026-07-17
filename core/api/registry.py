"""Generated REGOS API service registry."""
# Generated from REGOS public Swagger by tools/generate_regos_public_api.py.

from __future__ import annotations

from types import SimpleNamespace

from core.api.references.account import AccountService
from core.api.references.account_balance import AccountBalanceService
from core.api.references.account_operation_category import AccountOperationCategoryService
from core.api.common.action_log import ActionLogService
from core.api.rbac.application_setting import ApplicationSettingService
from core.api.references.barcode import BarcodeService
from core.api.references.barcode_type import BarcodeTypeService
from core.api.batch import BatchService
from core.api.references.brand import BrandService
from core.api.references.campaign import CampaignService
from core.api.docs.cash_operation import CashOperationService
from core.api.references.cash_server import CashServerService
from core.api.crm.channel import ChannelService
from core.api.chat.chat import ChatService
from core.api.chat.chat_message import ChatMessageService
from core.api.docs.cheque_item_operation import ChequeItemOperationService
from core.api.docs.cheque_operation import ChequeOperationService
from core.api.docs.cheque_payment_operation import ChequePaymentOperationService
from core.api.crm.client import ClientService
from core.api.references.color import ColorService
from core.api.docs.commercial_offer_operation import CommercialOfferOperationService
from core.api.integrations.connected_integration import ConnectedIntegrationService
from core.api.integrations.connected_integration_setting import ConnectedIntegrationSettingService
from core.api.references.country import CountryService
from core.api.references.currency import CurrencyService
from core.api.common.current_time_stamp import CurrentTimeStampService
from core.api.references.customer_personal_document import CustomerPersonalDocumentService
from core.api.widgets.dashboard import DashboardService
from core.api.crm.deal import DealService
from core.api.crm.deal_type import DealTypeService
from core.api.references.delivery_courier import DeliveryCourierService
from core.api.references.delivery_from import DeliveryFromService
from core.api.references.delivery_type import DeliveryTypeService
from core.api.references.department import DepartmentService
from core.api.docs.doc_account_movement import DocAccountMovementService
from core.api.docs.doc_additional_expenses import DocAdditionalExpensesService
from core.api.docs.doc_additional_expenses_operation import DocAdditionalExpensesOperationService
from core.api.docs.doc_cash_session import DocCashSessionService
from core.api.docs.doc_cheque import DocChequeService
from core.api.docs.doc_commercial_offer import DocCommercialOfferService
from core.api.docs.doc_contract import DocContractService
from core.api.docs.doc_contract_file import DocContractFileService
from core.api.docs.doc_in_out import DocInOutService
from core.api.docs.doc_inventory import DocInventoryService
from core.api.docs.doc_invoice import DocInvoiceService
from core.api.docs.doc_movement import DocMovementService
from core.api.docs.doc_opening_balance import DocOpeningBalanceService
from core.api.docs.doc_order_delivery import DocOrderDeliveryService
from core.api.docs.doc_order_from_partner import DocOrderFromPartnerService
from core.api.docs.doc_order_to_movement import DocOrderToMovementService
from core.api.docs.doc_order_to_partner import DocOrderToPartnerService
from core.api.docs.doc_payment import DocPaymentService
from core.api.docs.doc_payment_aggregation import DocPaymentAggregationService
from core.api.docs.doc_period_closing import DocPeriodClosingService
from core.api.rbac.doc_print_form import DocPrintFormService
from core.api.docs.doc_production import DocProductionService
from core.api.docs.doc_purchase import DocPurchaseService
from core.api.docs.doc_returns_to_partner import DocReturnsToPartnerService
from core.api.docs.doc_set_price import DocSetPriceService
from core.api.docs.doc_stock_aggregation import DocStockAggregationService
from core.api.docs.doc_tech_map import DocTechMapService
from core.api.docs.doc_whole_sale import DocWholeSaleService
from core.api.docs.doc_whole_sale_return import DocWholeSaleReturnService
from core.api.rbac.document_enumerator import DocumentEnumeratorService
from core.api.docs.document_status import DocumentStatusService
from core.api.docs.document_type import DocumentTypeService
from core.api.references.edited_exchange_rate_log import EditedExchangeRateLogService
from core.api.event.event import EventService
from core.api.docs.fast_group import FastGroupService
from core.api.docs.fast_item import FastItemService
from core.api.references.field import FieldService
from core.api.files.file import FileService
from core.api.common.filter import FilterService
from core.api.references.firm import FirmService
from core.api.references.firm_group import FirmGroupService
from core.api.files.folder import FolderService
from core.api.docs.in_out_operation import InOutOperationService
from core.api.integrations.integration import IntegrationService
from core.api.integrations.integration_group import IntegrationGroupService
from core.api.integrations.integration_webhook import IntegrationWebhookService
from core.api.docs.inventory_operation import InventoryOperationService
from core.api.docs.invoice_operation import InvoiceOperationService
from core.api.references.item import ItemService
from core.api.references.item_group import ItemGroupService
from core.api.references.item_image import ItemImageService
from core.api.references.item_operation import ItemOperationService
from core.api.references.item_price import ItemPriceService
from core.api.references.item_price_log import ItemPriceLogService
from core.api.rbac.language import LanguageService
from core.api.crm.lead import LeadService
from core.api.docs.movement_operation import MovementOperationService
from core.api.references.operating_cash import OperatingCashService
from core.api.docs.order_delivery_operation import OrderDeliveryOperationService
from core.api.docs.order_from_partner_operation import OrderFromPartnerOperationService
from core.api.docs.order_to_movement_operation import OrderToMovementOperationService
from core.api.docs.order_to_partner_operation import OrderToPartnerOperationService
from core.api.references.partner import PartnerService
from core.api.references.partner_balance import PartnerBalanceService
from core.api.references.partner_group import PartnerGroupService
from core.api.references.payment_type import PaymentTypeService
from core.api.rbac.permission_group import PermissionGroupService
from core.api.references.personal_doc_type import PersonalDocTypeService
from core.api.crm.pipeline import PipelineService
from core.api.docs.pos_cash_operation import PosCashOperationService
from core.api.docs.pos_doc_cheque import PosDocChequeService
from core.api.docs.pos_doc_order_delivery import PosDocOrderDeliveryService
from core.api.docs.pos_doc_session import PosDocSessionService
from core.api.references.pos_operating_cash import PosOperatingCashService
from core.api.references.price_type import PriceTypeService
from core.api.rbac.print_form_type import PrintFormTypeService
from core.api.references.producer import ProducerService
from core.api.docs.production_operation import ProductionOperationService
from core.api.crm.project import ProjectService
from core.api.crm.project_task import ProjectTaskService
from core.api.references.promo_bonus import PromoBonusService
from core.api.references.promo_program import PromoProgramService
from core.api.references.promo_program_setting import PromoProgramSettingService
from core.api.references.promo_program_stock import PromoProgramStockService
from core.api.references.promo_program_type import PromoProgramTypeService
from core.api.docs.purchase_operation import PurchaseOperationService
from core.api.chat.quick_reply import QuickReplyService
from core.api.common.redefinition import RedefinitionService
from core.api.references.region import RegionService
from core.api.reports.report import ReportService
from core.api.reports.report_prepared import ReportPreparedService
from core.api.reports.report_request import ReportRequestService
from core.api.references.retail_card import RetailCardService
from core.api.references.retail_card_group import RetailCardGroupService
from core.api.references.retail_card_migration import RetailCardMigrationService
from core.api.references.retail_customer import RetailCustomerService
from core.api.references.retail_customer_group import RetailCustomerGroupService
from core.api.docs.retail_operation_list import RetailOperationListService
from core.api.docs.retail_payment_report import RetailPaymentReportService
from core.api.docs.retail_report import RetailReportService
from core.api.references.retail_return_reason import RetailReturnReasonService
from core.api.docs.returns_to_partner_operation import ReturnsToPartnerOperationService
from core.api.rbac.role import RoleService
from core.api.rbac.role_permission import RolePermissionService
from core.api.rbac.session import SessionService
from core.api.docs.set_price_operation import SetPriceOperationService
from core.api.references.size_chart import SizeChartService
from core.api.references.sms import SmsService
from core.api.references.stock import StockService
from core.api.docs.stock_agregation_operation import StockAgregationOperationService
from core.api.files.storage import StorageService
from core.api.common.sys import SysService
from core.api.rbac.sys_config import SysConfigService
from core.api.rbac.tag import TagService
from core.api.references.target import TargetService
from core.api.references.target_setting import TargetSettingService
from core.api.references.target_type import TargetTypeService
from core.api.references.tax_vat import TaxVatService
from core.api.docs.tech_map_operation import TechMapOperationService
from core.api.crm.ticket import TicketService
from core.api.rbac.translation import TranslationService
from core.api.references.unit import UnitService
from core.api.rbac.user import UserService
from core.api.rbac.user_account import UserAccountService
from core.api.widgets.user_dashboard import UserDashboardService
from core.api.rbac.user_group import UserGroupService
from core.api.rbac.user_group_role import UserGroupRoleService
from core.api.rbac.user_notify import UserNotifyService
from core.api.rbac.user_operating_cash import UserOperatingCashService
from core.api.rbac.user_permission import UserPermissionService
from core.api.rbac.user_role import UserRoleService
from core.api.rbac.user_stock import UserStockService
from core.api.webhooks.webhook import WebhookService
from core.api.docs.whole_sale_operation import WholeSaleOperationService
from core.api.docs.whole_sale_return_operation import WholeSaleReturnOperationService
from core.api.widgets.widget import WidgetService
from core.api.widgets.widget_data import WidgetDataService
from core.api.widgets.widget_type import WidgetTypeService
from core.api.rbac.work_attendance import WorkAttendanceService
from core.api.rbac.work_schedule import WorkScheduleService
from core.api.rbac.work_schedule_assignment import WorkScheduleAssignmentService


def _ensure_namespace(api, name: str) -> SimpleNamespace:
    namespace = getattr(api, name, None)
    if namespace is None:
        namespace = SimpleNamespace()
        setattr(api, name, namespace)
    return namespace


def attach_generated_services(api) -> None:
    api.by_tag = getattr(api, 'by_tag', SimpleNamespace())
    _ensure_namespace(api, 'chat')
    _ensure_namespace(api, 'common')
    _ensure_namespace(api, 'crm')
    _ensure_namespace(api, 'docs')
    _ensure_namespace(api, 'event')
    _ensure_namespace(api, 'files')
    _ensure_namespace(api, 'integrations')
    _ensure_namespace(api, 'rbac')
    _ensure_namespace(api, 'references')
    _ensure_namespace(api, 'reports')
    _ensure_namespace(api, 'root')
    _ensure_namespace(api, 'webhooks')
    _ensure_namespace(api, 'widgets')

    _account_service = AccountService(api)
    setattr(api.references, 'account', _account_service)
    setattr(api.by_tag, 'account', _account_service)
    setattr(api, 'account', _account_service)
    _account_balance_service = AccountBalanceService(api)
    setattr(api.references, 'account_balance', _account_balance_service)
    setattr(api.by_tag, 'account_balance', _account_balance_service)
    setattr(api, 'account_balance', _account_balance_service)
    _account_operation_category_service = AccountOperationCategoryService(api)
    setattr(api.references, 'account_operation_category', _account_operation_category_service)
    setattr(api.by_tag, 'account_operation_category', _account_operation_category_service)
    setattr(api, 'account_operation_category', _account_operation_category_service)
    _action_log_service = ActionLogService(api)
    setattr(api.common, 'action_log', _action_log_service)
    setattr(api.by_tag, 'action_log', _action_log_service)
    setattr(api, 'action_log', _action_log_service)
    _application_setting_service = ApplicationSettingService(api)
    setattr(api.rbac, 'application_setting', _application_setting_service)
    setattr(api.by_tag, 'application_setting', _application_setting_service)
    setattr(api, 'application_setting', _application_setting_service)
    _barcode_service = BarcodeService(api)
    setattr(api.references, 'barcode', _barcode_service)
    setattr(api.by_tag, 'barcode', _barcode_service)
    setattr(api, 'barcode', _barcode_service)
    _barcode_type_service = BarcodeTypeService(api)
    setattr(api.references, 'barcode_type', _barcode_type_service)
    setattr(api.by_tag, 'barcode_type', _barcode_type_service)
    setattr(api, 'barcode_type', _barcode_type_service)
    _batch_service = BatchService(api)
    setattr(api.root, 'batch', _batch_service)
    setattr(api.by_tag, 'batch', _batch_service)
    setattr(api, 'batch', _batch_service)
    _brand_service = BrandService(api)
    setattr(api.references, 'brand', _brand_service)
    setattr(api.by_tag, 'brand', _brand_service)
    setattr(api, 'brand', _brand_service)
    _campaign_service = CampaignService(api)
    setattr(api.references, 'campaign', _campaign_service)
    setattr(api.by_tag, 'campaign', _campaign_service)
    setattr(api, 'campaign', _campaign_service)
    _cash_operation_service = CashOperationService(api)
    setattr(api.docs, 'cash_operation', _cash_operation_service)
    setattr(api.by_tag, 'cash_operation', _cash_operation_service)
    setattr(api, 'cash_operation', _cash_operation_service)
    _cash_server_service = CashServerService(api)
    setattr(api.references, 'cash_server', _cash_server_service)
    setattr(api.by_tag, 'cash_server', _cash_server_service)
    setattr(api, 'cash_server', _cash_server_service)
    _channel_service = ChannelService(api)
    setattr(api.crm, 'channel', _channel_service)
    setattr(api.by_tag, 'channel', _channel_service)
    setattr(api, 'channel', _channel_service)
    _chat_service = ChatService(api)
    setattr(api.chat, 'chat', _chat_service)
    setattr(api.by_tag, 'chat', _chat_service)
    setattr(api, 'chat_service', _chat_service)
    _chat_message_service = ChatMessageService(api)
    setattr(api.chat, 'chat_message', _chat_message_service)
    setattr(api.by_tag, 'chat_message', _chat_message_service)
    setattr(api, 'chat_message', _chat_message_service)
    _cheque_item_operation_service = ChequeItemOperationService(api)
    setattr(api.docs, 'cheque_item_operation', _cheque_item_operation_service)
    setattr(api.by_tag, 'cheque_item_operation', _cheque_item_operation_service)
    setattr(api, 'cheque_item_operation', _cheque_item_operation_service)
    _cheque_operation_service = ChequeOperationService(api)
    setattr(api.docs, 'cheque_operation', _cheque_operation_service)
    setattr(api.by_tag, 'cheque_operation', _cheque_operation_service)
    setattr(api, 'cheque_operation', _cheque_operation_service)
    _cheque_payment_operation_service = ChequePaymentOperationService(api)
    setattr(api.docs, 'cheque_payment_operation', _cheque_payment_operation_service)
    setattr(api.by_tag, 'cheque_payment_operation', _cheque_payment_operation_service)
    setattr(api, 'cheque_payment_operation', _cheque_payment_operation_service)
    _client_service = ClientService(api)
    setattr(api.crm, 'client', _client_service)
    setattr(api.by_tag, 'client', _client_service)
    setattr(api, 'client', _client_service)
    _color_service = ColorService(api)
    setattr(api.references, 'color', _color_service)
    setattr(api.by_tag, 'color', _color_service)
    setattr(api, 'color', _color_service)
    _commercial_offer_operation_service = CommercialOfferOperationService(api)
    setattr(api.docs, 'commercial_offer_operation', _commercial_offer_operation_service)
    setattr(api.by_tag, 'commercial_offer_operation', _commercial_offer_operation_service)
    setattr(api, 'commercial_offer_operation', _commercial_offer_operation_service)
    _connected_integration_service = ConnectedIntegrationService(api)
    setattr(api.integrations, 'connected_integration', _connected_integration_service)
    setattr(api.by_tag, 'connected_integration', _connected_integration_service)
    setattr(api, 'connected_integration', _connected_integration_service)
    _connected_integration_setting_service = ConnectedIntegrationSettingService(api)
    setattr(api.integrations, 'connected_integration_setting', _connected_integration_setting_service)
    setattr(api.by_tag, 'connected_integration_setting', _connected_integration_setting_service)
    setattr(api, 'connected_integration_setting', _connected_integration_setting_service)
    _country_service = CountryService(api)
    setattr(api.references, 'country', _country_service)
    setattr(api.by_tag, 'country', _country_service)
    setattr(api, 'country', _country_service)
    _currency_service = CurrencyService(api)
    setattr(api.references, 'currency', _currency_service)
    setattr(api.by_tag, 'currency', _currency_service)
    setattr(api, 'currency', _currency_service)
    _current_time_stamp_service = CurrentTimeStampService(api)
    setattr(api.common, 'current_time_stamp', _current_time_stamp_service)
    setattr(api.by_tag, 'current_time_stamp', _current_time_stamp_service)
    setattr(api, 'current_time_stamp', _current_time_stamp_service)
    _customer_personal_document_service = CustomerPersonalDocumentService(api)
    setattr(api.references, 'customer_personal_document', _customer_personal_document_service)
    setattr(api.by_tag, 'customer_personal_document', _customer_personal_document_service)
    setattr(api, 'customer_personal_document', _customer_personal_document_service)
    _dashboard_service = DashboardService(api)
    setattr(api.widgets, 'dashboard', _dashboard_service)
    setattr(api.by_tag, 'dashboard', _dashboard_service)
    setattr(api, 'dashboard', _dashboard_service)
    _deal_service = DealService(api)
    setattr(api.crm, 'deal', _deal_service)
    setattr(api.by_tag, 'deal', _deal_service)
    setattr(api, 'deal', _deal_service)
    _deal_type_service = DealTypeService(api)
    setattr(api.crm, 'deal_type', _deal_type_service)
    setattr(api.by_tag, 'deal_type', _deal_type_service)
    setattr(api, 'deal_type', _deal_type_service)
    _delivery_courier_service = DeliveryCourierService(api)
    setattr(api.references, 'delivery_courier', _delivery_courier_service)
    setattr(api.by_tag, 'delivery_courier', _delivery_courier_service)
    setattr(api, 'delivery_courier', _delivery_courier_service)
    _delivery_from_service = DeliveryFromService(api)
    setattr(api.references, 'delivery_from', _delivery_from_service)
    setattr(api.by_tag, 'delivery_from', _delivery_from_service)
    setattr(api, 'delivery_from', _delivery_from_service)
    _delivery_type_service = DeliveryTypeService(api)
    setattr(api.references, 'delivery_type', _delivery_type_service)
    setattr(api.by_tag, 'delivery_type', _delivery_type_service)
    setattr(api, 'delivery_type', _delivery_type_service)
    _department_service = DepartmentService(api)
    setattr(api.references, 'department', _department_service)
    setattr(api.by_tag, 'department', _department_service)
    setattr(api, 'department', _department_service)
    _doc_account_movement_service = DocAccountMovementService(api)
    setattr(api.docs, 'doc_account_movement', _doc_account_movement_service)
    setattr(api.by_tag, 'doc_account_movement', _doc_account_movement_service)
    setattr(api, 'doc_account_movement', _doc_account_movement_service)
    _doc_additional_expenses_service = DocAdditionalExpensesService(api)
    setattr(api.docs, 'doc_additional_expenses', _doc_additional_expenses_service)
    setattr(api.by_tag, 'doc_additional_expenses', _doc_additional_expenses_service)
    setattr(api, 'doc_additional_expenses', _doc_additional_expenses_service)
    _doc_additional_expenses_operation_service = DocAdditionalExpensesOperationService(api)
    setattr(api.docs, 'doc_additional_expenses_operation', _doc_additional_expenses_operation_service)
    setattr(api.by_tag, 'doc_additional_expenses_operation', _doc_additional_expenses_operation_service)
    setattr(api, 'doc_additional_expenses_operation', _doc_additional_expenses_operation_service)
    _doc_cash_session_service = DocCashSessionService(api)
    setattr(api.docs, 'doc_cash_session', _doc_cash_session_service)
    setattr(api.by_tag, 'doc_cash_session', _doc_cash_session_service)
    setattr(api, 'doc_cash_session', _doc_cash_session_service)
    _doc_cheque_service = DocChequeService(api)
    setattr(api.docs, 'doc_cheque', _doc_cheque_service)
    setattr(api.by_tag, 'doc_cheque', _doc_cheque_service)
    setattr(api, 'doc_cheque', _doc_cheque_service)
    _doc_commercial_offer_service = DocCommercialOfferService(api)
    setattr(api.docs, 'doc_commercial_offer', _doc_commercial_offer_service)
    setattr(api.by_tag, 'doc_commercial_offer', _doc_commercial_offer_service)
    setattr(api, 'doc_commercial_offer', _doc_commercial_offer_service)
    _doc_contract_service = DocContractService(api)
    setattr(api.docs, 'doc_contract', _doc_contract_service)
    setattr(api.by_tag, 'doc_contract', _doc_contract_service)
    setattr(api, 'doc_contract', _doc_contract_service)
    _doc_contract_file_service = DocContractFileService(api)
    setattr(api.docs, 'doc_contract_file', _doc_contract_file_service)
    setattr(api.by_tag, 'doc_contract_file', _doc_contract_file_service)
    setattr(api, 'doc_contract_file', _doc_contract_file_service)
    _doc_in_out_service = DocInOutService(api)
    setattr(api.docs, 'doc_in_out', _doc_in_out_service)
    setattr(api.by_tag, 'doc_in_out', _doc_in_out_service)
    setattr(api, 'doc_in_out', _doc_in_out_service)
    _doc_inventory_service = DocInventoryService(api)
    setattr(api.docs, 'doc_inventory', _doc_inventory_service)
    setattr(api.by_tag, 'doc_inventory', _doc_inventory_service)
    setattr(api, 'doc_inventory', _doc_inventory_service)
    _doc_invoice_service = DocInvoiceService(api)
    setattr(api.docs, 'doc_invoice', _doc_invoice_service)
    setattr(api.by_tag, 'doc_invoice', _doc_invoice_service)
    setattr(api, 'doc_invoice', _doc_invoice_service)
    _doc_movement_service = DocMovementService(api)
    setattr(api.docs, 'doc_movement', _doc_movement_service)
    setattr(api.by_tag, 'doc_movement', _doc_movement_service)
    setattr(api, 'doc_movement', _doc_movement_service)
    _doc_opening_balance_service = DocOpeningBalanceService(api)
    setattr(api.docs, 'doc_opening_balance', _doc_opening_balance_service)
    setattr(api.by_tag, 'doc_opening_balance', _doc_opening_balance_service)
    setattr(api, 'doc_opening_balance', _doc_opening_balance_service)
    _doc_order_delivery_service = DocOrderDeliveryService(api)
    setattr(api.docs, 'doc_order_delivery', _doc_order_delivery_service)
    setattr(api.by_tag, 'doc_order_delivery', _doc_order_delivery_service)
    setattr(api, 'doc_order_delivery', _doc_order_delivery_service)
    _doc_order_from_partner_service = DocOrderFromPartnerService(api)
    setattr(api.docs, 'doc_order_from_partner', _doc_order_from_partner_service)
    setattr(api.by_tag, 'doc_order_from_partner', _doc_order_from_partner_service)
    setattr(api, 'doc_order_from_partner', _doc_order_from_partner_service)
    _doc_order_to_movement_service = DocOrderToMovementService(api)
    setattr(api.docs, 'doc_order_to_movement', _doc_order_to_movement_service)
    setattr(api.by_tag, 'doc_order_to_movement', _doc_order_to_movement_service)
    setattr(api, 'doc_order_to_movement', _doc_order_to_movement_service)
    _doc_order_to_partner_service = DocOrderToPartnerService(api)
    setattr(api.docs, 'doc_order_to_partner', _doc_order_to_partner_service)
    setattr(api.by_tag, 'doc_order_to_partner', _doc_order_to_partner_service)
    setattr(api, 'doc_order_to_partner', _doc_order_to_partner_service)
    _doc_payment_service = DocPaymentService(api)
    setattr(api.docs, 'doc_payment', _doc_payment_service)
    setattr(api.by_tag, 'doc_payment', _doc_payment_service)
    setattr(api, 'doc_payment', _doc_payment_service)
    _doc_payment_aggregation_service = DocPaymentAggregationService(api)
    setattr(api.docs, 'doc_payment_aggregation', _doc_payment_aggregation_service)
    setattr(api.by_tag, 'doc_payment_aggregation', _doc_payment_aggregation_service)
    setattr(api, 'doc_payment_aggregation', _doc_payment_aggregation_service)
    _doc_period_closing_service = DocPeriodClosingService(api)
    setattr(api.docs, 'doc_period_closing', _doc_period_closing_service)
    setattr(api.by_tag, 'doc_period_closing', _doc_period_closing_service)
    setattr(api, 'doc_period_closing', _doc_period_closing_service)
    _doc_print_form_service = DocPrintFormService(api)
    setattr(api.rbac, 'doc_print_form', _doc_print_form_service)
    setattr(api.by_tag, 'doc_print_form', _doc_print_form_service)
    setattr(api, 'doc_print_form', _doc_print_form_service)
    _doc_production_service = DocProductionService(api)
    setattr(api.docs, 'doc_production', _doc_production_service)
    setattr(api.by_tag, 'doc_production', _doc_production_service)
    setattr(api, 'doc_production', _doc_production_service)
    _doc_purchase_service = DocPurchaseService(api)
    setattr(api.docs, 'doc_purchase', _doc_purchase_service)
    setattr(api.by_tag, 'doc_purchase', _doc_purchase_service)
    setattr(api, 'doc_purchase', _doc_purchase_service)
    _doc_returns_to_partner_service = DocReturnsToPartnerService(api)
    setattr(api.docs, 'doc_returns_to_partner', _doc_returns_to_partner_service)
    setattr(api.by_tag, 'doc_returns_to_partner', _doc_returns_to_partner_service)
    setattr(api, 'doc_returns_to_partner', _doc_returns_to_partner_service)
    _doc_set_price_service = DocSetPriceService(api)
    setattr(api.docs, 'doc_set_price', _doc_set_price_service)
    setattr(api.by_tag, 'doc_set_price', _doc_set_price_service)
    setattr(api, 'doc_set_price', _doc_set_price_service)
    _doc_stock_aggregation_service = DocStockAggregationService(api)
    setattr(api.docs, 'doc_stock_aggregation', _doc_stock_aggregation_service)
    setattr(api.by_tag, 'doc_stock_aggregation', _doc_stock_aggregation_service)
    setattr(api, 'doc_stock_aggregation', _doc_stock_aggregation_service)
    _doc_tech_map_service = DocTechMapService(api)
    setattr(api.docs, 'doc_tech_map', _doc_tech_map_service)
    setattr(api.by_tag, 'doc_tech_map', _doc_tech_map_service)
    setattr(api, 'doc_tech_map', _doc_tech_map_service)
    _doc_whole_sale_service = DocWholeSaleService(api)
    setattr(api.docs, 'doc_whole_sale', _doc_whole_sale_service)
    setattr(api.by_tag, 'doc_whole_sale', _doc_whole_sale_service)
    setattr(api, 'doc_whole_sale', _doc_whole_sale_service)
    _doc_whole_sale_return_service = DocWholeSaleReturnService(api)
    setattr(api.docs, 'doc_whole_sale_return', _doc_whole_sale_return_service)
    setattr(api.by_tag, 'doc_whole_sale_return', _doc_whole_sale_return_service)
    setattr(api, 'doc_whole_sale_return', _doc_whole_sale_return_service)
    _document_enumerator_service = DocumentEnumeratorService(api)
    setattr(api.rbac, 'document_enumerator', _document_enumerator_service)
    setattr(api.by_tag, 'document_enumerator', _document_enumerator_service)
    setattr(api, 'document_enumerator', _document_enumerator_service)
    _document_status_service = DocumentStatusService(api)
    setattr(api.docs, 'document_status', _document_status_service)
    setattr(api.by_tag, 'document_status', _document_status_service)
    setattr(api, 'document_status', _document_status_service)
    _document_type_service = DocumentTypeService(api)
    setattr(api.docs, 'document_type', _document_type_service)
    setattr(api.by_tag, 'document_type', _document_type_service)
    setattr(api, 'document_type', _document_type_service)
    _edited_exchange_rate_log_service = EditedExchangeRateLogService(api)
    setattr(api.references, 'edited_exchange_rate_log', _edited_exchange_rate_log_service)
    setattr(api.by_tag, 'edited_exchange_rate_log', _edited_exchange_rate_log_service)
    setattr(api, 'edited_exchange_rate_log', _edited_exchange_rate_log_service)
    _event_service = EventService(api)
    setattr(api.event, 'event', _event_service)
    setattr(api.by_tag, 'event', _event_service)
    setattr(api, 'event_service', _event_service)
    _fast_group_service = FastGroupService(api)
    setattr(api.docs, 'fast_group', _fast_group_service)
    setattr(api.by_tag, 'fast_group', _fast_group_service)
    setattr(api, 'fast_group', _fast_group_service)
    _fast_item_service = FastItemService(api)
    setattr(api.docs, 'fast_item', _fast_item_service)
    setattr(api.by_tag, 'fast_item', _fast_item_service)
    setattr(api, 'fast_item', _fast_item_service)
    _field_service = FieldService(api)
    setattr(api.references, 'field', _field_service)
    setattr(api.by_tag, 'field', _field_service)
    setattr(api, 'field', _field_service)
    _file_service = FileService(api)
    setattr(api.files, 'file', _file_service)
    setattr(api.by_tag, 'file', _file_service)
    setattr(api, 'file', _file_service)
    _filter_service = FilterService(api)
    setattr(api.common, 'filter', _filter_service)
    setattr(api.by_tag, 'filter', _filter_service)
    setattr(api, 'filter', _filter_service)
    _firm_service = FirmService(api)
    setattr(api.references, 'firm', _firm_service)
    setattr(api.by_tag, 'firm', _firm_service)
    setattr(api, 'firm', _firm_service)
    _firm_group_service = FirmGroupService(api)
    setattr(api.references, 'firm_group', _firm_group_service)
    setattr(api.by_tag, 'firm_group', _firm_group_service)
    setattr(api, 'firm_group', _firm_group_service)
    _folder_service = FolderService(api)
    setattr(api.files, 'folder', _folder_service)
    setattr(api.by_tag, 'folder', _folder_service)
    setattr(api, 'folder', _folder_service)
    _in_out_operation_service = InOutOperationService(api)
    setattr(api.docs, 'in_out_operation', _in_out_operation_service)
    setattr(api.by_tag, 'in_out_operation', _in_out_operation_service)
    setattr(api, 'in_out_operation', _in_out_operation_service)
    _integration_service = IntegrationService(api)
    setattr(api.integrations, 'integration', _integration_service)
    setattr(api.by_tag, 'integration', _integration_service)
    setattr(api, 'integration', _integration_service)
    _integration_group_service = IntegrationGroupService(api)
    setattr(api.integrations, 'integration_group', _integration_group_service)
    setattr(api.by_tag, 'integration_group', _integration_group_service)
    setattr(api, 'integration_group', _integration_group_service)
    _integration_webhook_service = IntegrationWebhookService(api)
    setattr(api.integrations, 'integration_webhook', _integration_webhook_service)
    setattr(api.by_tag, 'integration_webhook', _integration_webhook_service)
    setattr(api, 'integration_webhook', _integration_webhook_service)
    _inventory_operation_service = InventoryOperationService(api)
    setattr(api.docs, 'inventory_operation', _inventory_operation_service)
    setattr(api.by_tag, 'inventory_operation', _inventory_operation_service)
    setattr(api, 'inventory_operation', _inventory_operation_service)
    _invoice_operation_service = InvoiceOperationService(api)
    setattr(api.docs, 'invoice_operation', _invoice_operation_service)
    setattr(api.by_tag, 'invoice_operation', _invoice_operation_service)
    setattr(api, 'invoice_operation', _invoice_operation_service)
    _item_service = ItemService(api)
    setattr(api.references, 'item', _item_service)
    setattr(api.by_tag, 'item', _item_service)
    setattr(api, 'item', _item_service)
    _item_group_service = ItemGroupService(api)
    setattr(api.references, 'item_group', _item_group_service)
    setattr(api.by_tag, 'item_group', _item_group_service)
    setattr(api, 'item_group', _item_group_service)
    _item_image_service = ItemImageService(api)
    setattr(api.references, 'item_image', _item_image_service)
    setattr(api.by_tag, 'item_image', _item_image_service)
    setattr(api, 'item_image', _item_image_service)
    _item_operation_service = ItemOperationService(api)
    setattr(api.references, 'item_operation', _item_operation_service)
    setattr(api.by_tag, 'item_operation', _item_operation_service)
    setattr(api, 'item_operation', _item_operation_service)
    _item_price_service = ItemPriceService(api)
    setattr(api.references, 'item_price', _item_price_service)
    setattr(api.by_tag, 'item_price', _item_price_service)
    setattr(api, 'item_price', _item_price_service)
    _item_price_log_service = ItemPriceLogService(api)
    setattr(api.references, 'item_price_log', _item_price_log_service)
    setattr(api.by_tag, 'item_price_log', _item_price_log_service)
    setattr(api, 'item_price_log', _item_price_log_service)
    _language_service = LanguageService(api)
    setattr(api.rbac, 'language', _language_service)
    setattr(api.by_tag, 'language', _language_service)
    setattr(api, 'language', _language_service)
    _lead_service = LeadService(api)
    setattr(api.crm, 'lead', _lead_service)
    setattr(api.by_tag, 'lead', _lead_service)
    setattr(api, 'lead', _lead_service)
    _movement_operation_service = MovementOperationService(api)
    setattr(api.docs, 'movement_operation', _movement_operation_service)
    setattr(api.by_tag, 'movement_operation', _movement_operation_service)
    setattr(api, 'movement_operation', _movement_operation_service)
    _operating_cash_service = OperatingCashService(api)
    setattr(api.references, 'operating_cash', _operating_cash_service)
    setattr(api.by_tag, 'operating_cash', _operating_cash_service)
    setattr(api, 'operating_cash', _operating_cash_service)
    _order_delivery_operation_service = OrderDeliveryOperationService(api)
    setattr(api.docs, 'order_delivery_operation', _order_delivery_operation_service)
    setattr(api.by_tag, 'order_delivery_operation', _order_delivery_operation_service)
    setattr(api, 'order_delivery_operation', _order_delivery_operation_service)
    _order_from_partner_operation_service = OrderFromPartnerOperationService(api)
    setattr(api.docs, 'order_from_partner_operation', _order_from_partner_operation_service)
    setattr(api.by_tag, 'order_from_partner_operation', _order_from_partner_operation_service)
    setattr(api, 'order_from_partner_operation', _order_from_partner_operation_service)
    _order_to_movement_operation_service = OrderToMovementOperationService(api)
    setattr(api.docs, 'order_to_movement_operation', _order_to_movement_operation_service)
    setattr(api.by_tag, 'order_to_movement_operation', _order_to_movement_operation_service)
    setattr(api, 'order_to_movement_operation', _order_to_movement_operation_service)
    _order_to_partner_operation_service = OrderToPartnerOperationService(api)
    setattr(api.docs, 'order_to_partner_operation', _order_to_partner_operation_service)
    setattr(api.by_tag, 'order_to_partner_operation', _order_to_partner_operation_service)
    setattr(api, 'order_to_partner_operation', _order_to_partner_operation_service)
    _partner_service = PartnerService(api)
    setattr(api.references, 'partner', _partner_service)
    setattr(api.by_tag, 'partner', _partner_service)
    setattr(api, 'partner', _partner_service)
    _partner_balance_service = PartnerBalanceService(api)
    setattr(api.references, 'partner_balance', _partner_balance_service)
    setattr(api.by_tag, 'partner_balance', _partner_balance_service)
    setattr(api, 'partner_balance', _partner_balance_service)
    _partner_group_service = PartnerGroupService(api)
    setattr(api.references, 'partner_group', _partner_group_service)
    setattr(api.by_tag, 'partner_group', _partner_group_service)
    setattr(api, 'partner_group', _partner_group_service)
    _payment_type_service = PaymentTypeService(api)
    setattr(api.references, 'payment_type', _payment_type_service)
    setattr(api.by_tag, 'payment_type', _payment_type_service)
    setattr(api, 'payment_type', _payment_type_service)
    _permission_group_service = PermissionGroupService(api)
    setattr(api.rbac, 'permission_group', _permission_group_service)
    setattr(api.by_tag, 'permission_group', _permission_group_service)
    setattr(api, 'permission_group', _permission_group_service)
    _personal_doc_type_service = PersonalDocTypeService(api)
    setattr(api.references, 'personal_doc_type', _personal_doc_type_service)
    setattr(api.by_tag, 'personal_doc_type', _personal_doc_type_service)
    setattr(api, 'personal_doc_type', _personal_doc_type_service)
    _pipeline_service = PipelineService(api)
    setattr(api.crm, 'pipeline', _pipeline_service)
    setattr(api.by_tag, 'pipeline', _pipeline_service)
    setattr(api, 'pipeline', _pipeline_service)
    _pos_cash_operation_service = PosCashOperationService(api)
    setattr(api.docs, 'pos_cash_operation', _pos_cash_operation_service)
    setattr(api.by_tag, 'pos_cash_operation', _pos_cash_operation_service)
    setattr(api, 'pos_cash_operation', _pos_cash_operation_service)
    _pos_doc_cheque_service = PosDocChequeService(api)
    setattr(api.docs, 'pos_doc_cheque', _pos_doc_cheque_service)
    setattr(api.by_tag, 'pos_doc_cheque', _pos_doc_cheque_service)
    setattr(api, 'pos_doc_cheque', _pos_doc_cheque_service)
    _pos_doc_order_delivery_service = PosDocOrderDeliveryService(api)
    setattr(api.docs, 'pos_doc_order_delivery', _pos_doc_order_delivery_service)
    setattr(api.by_tag, 'pos_doc_order_delivery', _pos_doc_order_delivery_service)
    setattr(api, 'pos_doc_order_delivery', _pos_doc_order_delivery_service)
    _pos_doc_session_service = PosDocSessionService(api)
    setattr(api.docs, 'pos_doc_session', _pos_doc_session_service)
    setattr(api.by_tag, 'pos_doc_session', _pos_doc_session_service)
    setattr(api, 'pos_doc_session', _pos_doc_session_service)
    _pos_operating_cash_service = PosOperatingCashService(api)
    setattr(api.references, 'pos_operating_cash', _pos_operating_cash_service)
    setattr(api.by_tag, 'pos_operating_cash', _pos_operating_cash_service)
    setattr(api, 'pos_operating_cash', _pos_operating_cash_service)
    _price_type_service = PriceTypeService(api)
    setattr(api.references, 'price_type', _price_type_service)
    setattr(api.by_tag, 'price_type', _price_type_service)
    setattr(api, 'price_type', _price_type_service)
    _print_form_type_service = PrintFormTypeService(api)
    setattr(api.rbac, 'print_form_type', _print_form_type_service)
    setattr(api.by_tag, 'print_form_type', _print_form_type_service)
    setattr(api, 'print_form_type', _print_form_type_service)
    _producer_service = ProducerService(api)
    setattr(api.references, 'producer', _producer_service)
    setattr(api.by_tag, 'producer', _producer_service)
    setattr(api, 'producer', _producer_service)
    _production_operation_service = ProductionOperationService(api)
    setattr(api.docs, 'production_operation', _production_operation_service)
    setattr(api.by_tag, 'production_operation', _production_operation_service)
    setattr(api, 'production_operation', _production_operation_service)
    _project_service = ProjectService(api)
    setattr(api.crm, 'project', _project_service)
    setattr(api.by_tag, 'project', _project_service)
    setattr(api, 'project', _project_service)
    _project_task_service = ProjectTaskService(api)
    setattr(api.crm, 'project_task', _project_task_service)
    setattr(api.by_tag, 'project_task', _project_task_service)
    setattr(api, 'project_task', _project_task_service)
    _promo_bonus_service = PromoBonusService(api)
    setattr(api.references, 'promo_bonus', _promo_bonus_service)
    setattr(api.by_tag, 'promo_bonus', _promo_bonus_service)
    setattr(api, 'promo_bonus', _promo_bonus_service)
    _promo_program_service = PromoProgramService(api)
    setattr(api.references, 'promo_program', _promo_program_service)
    setattr(api.by_tag, 'promo_program', _promo_program_service)
    setattr(api, 'promo_program', _promo_program_service)
    _promo_program_setting_service = PromoProgramSettingService(api)
    setattr(api.references, 'promo_program_setting', _promo_program_setting_service)
    setattr(api.by_tag, 'promo_program_setting', _promo_program_setting_service)
    setattr(api, 'promo_program_setting', _promo_program_setting_service)
    _promo_program_stock_service = PromoProgramStockService(api)
    setattr(api.references, 'promo_program_stock', _promo_program_stock_service)
    setattr(api.by_tag, 'promo_program_stock', _promo_program_stock_service)
    setattr(api, 'promo_program_stock', _promo_program_stock_service)
    _promo_program_type_service = PromoProgramTypeService(api)
    setattr(api.references, 'promo_program_type', _promo_program_type_service)
    setattr(api.by_tag, 'promo_program_type', _promo_program_type_service)
    setattr(api, 'promo_program_type', _promo_program_type_service)
    _purchase_operation_service = PurchaseOperationService(api)
    setattr(api.docs, 'purchase_operation', _purchase_operation_service)
    setattr(api.by_tag, 'purchase_operation', _purchase_operation_service)
    setattr(api, 'purchase_operation', _purchase_operation_service)
    _quick_reply_service = QuickReplyService(api)
    setattr(api.chat, 'quick_reply', _quick_reply_service)
    setattr(api.by_tag, 'quick_reply', _quick_reply_service)
    setattr(api, 'quick_reply', _quick_reply_service)
    _redefinition_service = RedefinitionService(api)
    setattr(api.common, 'redefinition', _redefinition_service)
    setattr(api.by_tag, 'redefinition', _redefinition_service)
    setattr(api, 'redefinition', _redefinition_service)
    _region_service = RegionService(api)
    setattr(api.references, 'region', _region_service)
    setattr(api.by_tag, 'region', _region_service)
    setattr(api, 'region', _region_service)
    _report_service = ReportService(api)
    setattr(api.reports, 'report', _report_service)
    setattr(api.by_tag, 'report', _report_service)
    setattr(api, 'report', _report_service)
    _report_prepared_service = ReportPreparedService(api)
    setattr(api.reports, 'report_prepared', _report_prepared_service)
    setattr(api.by_tag, 'report_prepared', _report_prepared_service)
    setattr(api, 'report_prepared', _report_prepared_service)
    _report_request_service = ReportRequestService(api)
    setattr(api.reports, 'report_request', _report_request_service)
    setattr(api.by_tag, 'report_request', _report_request_service)
    setattr(api, 'report_request', _report_request_service)
    _retail_card_service = RetailCardService(api)
    setattr(api.references, 'retail_card', _retail_card_service)
    setattr(api.by_tag, 'retail_card', _retail_card_service)
    setattr(api, 'retail_card', _retail_card_service)
    _retail_card_group_service = RetailCardGroupService(api)
    setattr(api.references, 'retail_card_group', _retail_card_group_service)
    setattr(api.by_tag, 'retail_card_group', _retail_card_group_service)
    setattr(api, 'retail_card_group', _retail_card_group_service)
    _retail_card_migration_service = RetailCardMigrationService(api)
    setattr(api.references, 'retail_card_migration', _retail_card_migration_service)
    setattr(api.by_tag, 'retail_card_migration', _retail_card_migration_service)
    setattr(api, 'retail_card_migration', _retail_card_migration_service)
    _retail_customer_service = RetailCustomerService(api)
    setattr(api.references, 'retail_customer', _retail_customer_service)
    setattr(api.by_tag, 'retail_customer', _retail_customer_service)
    setattr(api, 'retail_customer', _retail_customer_service)
    _retail_customer_group_service = RetailCustomerGroupService(api)
    setattr(api.references, 'retail_customer_group', _retail_customer_group_service)
    setattr(api.by_tag, 'retail_customer_group', _retail_customer_group_service)
    setattr(api, 'retail_customer_group', _retail_customer_group_service)
    _retail_operation_list_service = RetailOperationListService(api)
    setattr(api.docs, 'retail_operation_list', _retail_operation_list_service)
    setattr(api.by_tag, 'retail_operation_list', _retail_operation_list_service)
    setattr(api, 'retail_operation_list', _retail_operation_list_service)
    _retail_payment_report_service = RetailPaymentReportService(api)
    setattr(api.docs, 'retail_payment_report', _retail_payment_report_service)
    setattr(api.by_tag, 'retail_payment_report', _retail_payment_report_service)
    setattr(api, 'retail_payment_report', _retail_payment_report_service)
    _retail_report_service = RetailReportService(api)
    setattr(api.docs, 'retail_report', _retail_report_service)
    setattr(api.by_tag, 'retail_report', _retail_report_service)
    setattr(api, 'retail_report', _retail_report_service)
    _retail_return_reason_service = RetailReturnReasonService(api)
    setattr(api.references, 'retail_return_reason', _retail_return_reason_service)
    setattr(api.by_tag, 'retail_return_reason', _retail_return_reason_service)
    setattr(api, 'retail_return_reason', _retail_return_reason_service)
    _returns_to_partner_operation_service = ReturnsToPartnerOperationService(api)
    setattr(api.docs, 'returns_to_partner_operation', _returns_to_partner_operation_service)
    setattr(api.by_tag, 'returns_to_partner_operation', _returns_to_partner_operation_service)
    setattr(api, 'returns_to_partner_operation', _returns_to_partner_operation_service)
    _role_service = RoleService(api)
    setattr(api.rbac, 'role', _role_service)
    setattr(api.by_tag, 'role', _role_service)
    setattr(api, 'role', _role_service)
    _role_permission_service = RolePermissionService(api)
    setattr(api.rbac, 'role_permission', _role_permission_service)
    setattr(api.by_tag, 'role_permission', _role_permission_service)
    setattr(api, 'role_permission', _role_permission_service)
    _session_service = SessionService(api)
    setattr(api.rbac, 'session', _session_service)
    setattr(api.by_tag, 'session', _session_service)
    setattr(api, 'session', _session_service)
    _set_price_operation_service = SetPriceOperationService(api)
    setattr(api.docs, 'set_price_operation', _set_price_operation_service)
    setattr(api.by_tag, 'set_price_operation', _set_price_operation_service)
    setattr(api, 'set_price_operation', _set_price_operation_service)
    _size_chart_service = SizeChartService(api)
    setattr(api.references, 'size_chart', _size_chart_service)
    setattr(api.by_tag, 'size_chart', _size_chart_service)
    setattr(api, 'size_chart', _size_chart_service)
    _sms_service = SmsService(api)
    setattr(api.references, 'sms', _sms_service)
    setattr(api.by_tag, 'sms', _sms_service)
    setattr(api, 'sms', _sms_service)
    _stock_service = StockService(api)
    setattr(api.references, 'stock', _stock_service)
    setattr(api.by_tag, 'stock', _stock_service)
    setattr(api, 'stock', _stock_service)
    _stock_agregation_operation_service = StockAgregationOperationService(api)
    setattr(api.docs, 'stock_agregation_operation', _stock_agregation_operation_service)
    setattr(api.by_tag, 'stock_agregation_operation', _stock_agregation_operation_service)
    setattr(api, 'stock_agregation_operation', _stock_agregation_operation_service)
    _storage_service = StorageService(api)
    setattr(api.files, 'storage', _storage_service)
    setattr(api.by_tag, 'storage', _storage_service)
    setattr(api, 'storage', _storage_service)
    _sys_service = SysService(api)
    setattr(api.common, 'sys', _sys_service)
    setattr(api.by_tag, 'sys', _sys_service)
    setattr(api, 'sys', _sys_service)
    _sys_config_service = SysConfigService(api)
    setattr(api.rbac, 'sys_config', _sys_config_service)
    setattr(api.by_tag, 'sys_config', _sys_config_service)
    setattr(api, 'sys_config', _sys_config_service)
    _tag_service = TagService(api)
    setattr(api.rbac, 'tag', _tag_service)
    setattr(api.by_tag, 'tag', _tag_service)
    setattr(api, 'tag', _tag_service)
    _target_service = TargetService(api)
    setattr(api.references, 'target', _target_service)
    setattr(api.by_tag, 'target', _target_service)
    setattr(api, 'target', _target_service)
    _target_setting_service = TargetSettingService(api)
    setattr(api.references, 'target_setting', _target_setting_service)
    setattr(api.by_tag, 'target_setting', _target_setting_service)
    setattr(api, 'target_setting', _target_setting_service)
    _target_type_service = TargetTypeService(api)
    setattr(api.references, 'target_type', _target_type_service)
    setattr(api.by_tag, 'target_type', _target_type_service)
    setattr(api, 'target_type', _target_type_service)
    _tax_vat_service = TaxVatService(api)
    setattr(api.references, 'tax_vat', _tax_vat_service)
    setattr(api.by_tag, 'tax_vat', _tax_vat_service)
    setattr(api, 'tax_vat', _tax_vat_service)
    _tech_map_operation_service = TechMapOperationService(api)
    setattr(api.docs, 'tech_map_operation', _tech_map_operation_service)
    setattr(api.by_tag, 'tech_map_operation', _tech_map_operation_service)
    setattr(api, 'tech_map_operation', _tech_map_operation_service)
    _ticket_service = TicketService(api)
    setattr(api.crm, 'ticket', _ticket_service)
    setattr(api.by_tag, 'ticket', _ticket_service)
    setattr(api, 'ticket', _ticket_service)
    _translation_service = TranslationService(api)
    setattr(api.rbac, 'translation', _translation_service)
    setattr(api.by_tag, 'translation', _translation_service)
    setattr(api, 'translation', _translation_service)
    _unit_service = UnitService(api)
    setattr(api.references, 'unit', _unit_service)
    setattr(api.by_tag, 'unit', _unit_service)
    setattr(api, 'unit', _unit_service)
    _user_service = UserService(api)
    setattr(api.rbac, 'user', _user_service)
    setattr(api.by_tag, 'user', _user_service)
    setattr(api, 'user', _user_service)
    _user_account_service = UserAccountService(api)
    setattr(api.rbac, 'user_account', _user_account_service)
    setattr(api.by_tag, 'user_account', _user_account_service)
    setattr(api, 'user_account', _user_account_service)
    _user_dashboard_service = UserDashboardService(api)
    setattr(api.widgets, 'user_dashboard', _user_dashboard_service)
    setattr(api.by_tag, 'user_dashboard', _user_dashboard_service)
    setattr(api, 'user_dashboard', _user_dashboard_service)
    _user_group_service = UserGroupService(api)
    setattr(api.rbac, 'user_group', _user_group_service)
    setattr(api.by_tag, 'user_group', _user_group_service)
    setattr(api, 'user_group', _user_group_service)
    _user_group_role_service = UserGroupRoleService(api)
    setattr(api.rbac, 'user_group_role', _user_group_role_service)
    setattr(api.by_tag, 'user_group_role', _user_group_role_service)
    setattr(api, 'user_group_role', _user_group_role_service)
    _user_notify_service = UserNotifyService(api)
    setattr(api.rbac, 'user_notify', _user_notify_service)
    setattr(api.by_tag, 'user_notify', _user_notify_service)
    setattr(api, 'user_notify', _user_notify_service)
    _user_operating_cash_service = UserOperatingCashService(api)
    setattr(api.rbac, 'user_operating_cash', _user_operating_cash_service)
    setattr(api.by_tag, 'user_operating_cash', _user_operating_cash_service)
    setattr(api, 'user_operating_cash', _user_operating_cash_service)
    _user_permission_service = UserPermissionService(api)
    setattr(api.rbac, 'user_permission', _user_permission_service)
    setattr(api.by_tag, 'user_permission', _user_permission_service)
    setattr(api, 'user_permission', _user_permission_service)
    _user_role_service = UserRoleService(api)
    setattr(api.rbac, 'user_role', _user_role_service)
    setattr(api.by_tag, 'user_role', _user_role_service)
    setattr(api, 'user_role', _user_role_service)
    _user_stock_service = UserStockService(api)
    setattr(api.rbac, 'user_stock', _user_stock_service)
    setattr(api.by_tag, 'user_stock', _user_stock_service)
    setattr(api, 'user_stock', _user_stock_service)
    _webhook_service = WebhookService(api)
    setattr(api.webhooks, 'webhook', _webhook_service)
    setattr(api.by_tag, 'webhook', _webhook_service)
    setattr(api, 'webhook', _webhook_service)
    _whole_sale_operation_service = WholeSaleOperationService(api)
    setattr(api.docs, 'whole_sale_operation', _whole_sale_operation_service)
    setattr(api.by_tag, 'whole_sale_operation', _whole_sale_operation_service)
    setattr(api, 'whole_sale_operation', _whole_sale_operation_service)
    _whole_sale_return_operation_service = WholeSaleReturnOperationService(api)
    setattr(api.docs, 'whole_sale_return_operation', _whole_sale_return_operation_service)
    setattr(api.by_tag, 'whole_sale_return_operation', _whole_sale_return_operation_service)
    setattr(api, 'whole_sale_return_operation', _whole_sale_return_operation_service)
    _widget_service = WidgetService(api)
    setattr(api.widgets, 'widget', _widget_service)
    setattr(api.by_tag, 'widget', _widget_service)
    setattr(api, 'widget', _widget_service)
    _widget_data_service = WidgetDataService(api)
    setattr(api.widgets, 'widget_data', _widget_data_service)
    setattr(api.by_tag, 'widget_data', _widget_data_service)
    setattr(api, 'widget_data', _widget_data_service)
    _widget_type_service = WidgetTypeService(api)
    setattr(api.widgets, 'widget_type', _widget_type_service)
    setattr(api.by_tag, 'widget_type', _widget_type_service)
    setattr(api, 'widget_type', _widget_type_service)
    _work_attendance_service = WorkAttendanceService(api)
    setattr(api.rbac, 'work_attendance', _work_attendance_service)
    setattr(api.by_tag, 'work_attendance', _work_attendance_service)
    setattr(api, 'work_attendance', _work_attendance_service)
    _work_schedule_service = WorkScheduleService(api)
    setattr(api.rbac, 'work_schedule', _work_schedule_service)
    setattr(api.by_tag, 'work_schedule', _work_schedule_service)
    setattr(api, 'work_schedule', _work_schedule_service)
    _work_schedule_assignment_service = WorkScheduleAssignmentService(api)
    setattr(api.rbac, 'work_schedule_assignment', _work_schedule_assignment_service)
    setattr(api.by_tag, 'work_schedule_assignment', _work_schedule_assignment_service)
    setattr(api, 'work_schedule_assignment', _work_schedule_assignment_service)


__all__ = ['attach_generated_services']
