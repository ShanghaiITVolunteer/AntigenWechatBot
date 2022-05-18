import sys
sys.path.insert(0, '/Users/mcat/Code/shanghai-it-volunteer/AntigenWechatBot/ss/JuWeiHui')

from group_purchase.community.jia_yi_shui_an import JiaYiShuiAn
from group_purchase.purchase_deliver.parser_mng import get_excel_parser
from group_purchase.utils.utils import *


def test_excel_parser():
    """test group purshse code"""
    community = JiaYiShuiAn()
    excel_file = './tests/data/committee_data.xlsx'
    pdf_file = './tests/data/committee_data.pdf'
    parser = get_excel_parser('快团团')(open(excel_file, 'rb'))
    result, error = parser.parse_for_community(community)
    assert error is None
    assert result is not None
    result.print_to_pdf(pdf_file, False)
