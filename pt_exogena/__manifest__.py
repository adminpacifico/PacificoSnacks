# -*- coding: utf-8 -*-
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_edi_parati.  If not, see <https://www.gnu.org/licenses/>.
#
# email: administracion@parati.com.co
#
{
    'name': "Informacion Exogena",
    'summary': 'Informacion Exogena',
    'description': "Exportar Informacion Exogena para los diferentes formatos DIAN",
    'author': "Para TI.CO SAS",
    'license': "LGPL-3",
    'category': 'Sales',
    'version': '17.1',
    'website': "https://www.Parati.com.co",
    'images': ['static/images/main_screenshot.png'],
    'support': 'administracion@parati.com.co',

    # Odoo, OCA and dependencies
    'depends': [
        'account',
        'report_xlsx',
    ],
    'data': [
        'views/pt_exogena_report.xml',
        'views/pt_config_accounts_view.xml',
        'wizard/pt_exogena_wizard_view.xml',
        'report/pt_exogena_xlsx_report.xml',
    ],
    'installable': True,
    'application': True,
}
