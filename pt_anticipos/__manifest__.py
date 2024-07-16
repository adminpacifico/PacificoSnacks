# -*- coding: utf-8 -*-
#
# You should have received a copy of the GNU Lesser General Public License
# along with l10n_co_edi_parati.  If not, see <https://www.gnu.org/licenses/>.
#
# email: administracion@parati.com.co
#
{
    'name': "PT Anticipos por pagos",
    'summary': 'Account receivable and payable advance payments in another account by customer or vendor',
    'description': "Advance payments AR and AP",
    'author': "Para TI.CO SAS",
    'license': "LGPL-3",
    'category': 'Sales',
    'version': '17.1',
    'website': "https://www.Parati.com.co",
    'images': ['static/images/main_screenshot.png'],
    'support': 'administracion@parati.com.co',
    
    # Odoo, OCA and dependencies
    'depends': [
        'base',
        'account',
        'account_payment',
    ],
    'data': [
        'views/account_payment_view.xml',
        'views/res_partner_view.xml',
    ],
    'installable': True,
    'application': True,
}
