import requests
import datetime
from dbConfig import *

import logging
FORMAT = "[f360 fetch_fnz_mf] %(asctime)s - [%(funcName)s()] %(message)s"
logging.basicConfig(format=FORMAT, level=runtime_cfg.LOGLEVEL)
logger = logging.getLogger(__name__)


def read_from_ms_database():
    logger.info('Reading MS database for basic fund info')
    conn = get_ms_db_conn()

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            sql = 'SELECT f.MStarID, f.ISIN, f.BrandingName, fcm.FundName, fcm.FundName_CN, f.InvestmentStrategy, ' \
                  ' COALESCE(st.InvestmentStrategy_CHN, \'\') as InvestmentStrategy_CHN, ' \
                  ' COALESCE(ftc.InvestmentStrategy_TCHN, \'\') as InvestmentStrategy_TCHN, ' \
                  ' f.CategoryCode, f.BroadCategoryGroupID ' \
                  'from hkfundbasicinfo f ' \
                  ' LEFT JOIN hkfundchineseinvestmentstrategy st on f.mstarId = st.mstarId, ' \
                  ' hkfundchinesenamemapping fcm, hkfundtraditionalchinese ftc ' \
                  'where ' \
                  ' f.mstarId = fcm.mstarId ' \
                  ' and f.mstarId = ftc.mstarId '

            cursor.execute(sql)
            query_result = cursor.fetchall()
    finally:
        conn.close()

    result = {}
    #return dict((isin, {'mStarId': mStarId, 'strategy': strategy, 'mstar_category': mstar_category, 'branding': branding}) for isin, mStarId, strategy, mstar_category, branding in result)
    for item in query_result:
        result.setdefault(item['ISIN'], item)

    return result

def get_fnz_funds():
    logger.info('Getting FNZ Fund from ' + fnz_fund_api)
    #url = 'https://distributionserviceofsu36.fnz.com/api/distribution/v3/funds?ProductCode='+arg_instcode
    headers = {}
    headers['Content-Type'] = 'application/json'
    headers['X-ApplicationName'] = '1'
    headers['X-UserContext'] = 'UserId=436476'  # or UserId = 436477
    headers['Accept'] = 'application/json'
    req = requests.get(url=fnz_fund_api, headers=headers)
    r = req.json()
    if int(r['TotalNumberOfResults']) > 0:
        return r['PageOfResults']    # from a list of dictionary
    else:
        return []

def insert_mutual_funds(isin_map):
    logger.info('Inserting into mutual fund database')
    conn = get_fund_db_conn()
    cursor = conn.cursor()

    fund_name_sql = "REPLACE INTO mstar_fund_name(mstar_id, name, name_cn) values(%s, %s, %s)"
    mf_sql = "REPLACE INTO mutual_fund (name, product_id, isin, fnz_code, currency, inception_date, fund_size, investment_strategy, investment_strategy_cn, investment_strategy_tw, domicile, div_type, " \
             "asset_class, sub_asset_class, branding, company_name, primary_index, mstar_id, mstar_category_code, mstar_broad_category_group_id, buyable) " \
             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    charge_sql = "REPLACE INTO fund_charge (isin, initial_inv_amt, initial_charge, annual_charge, subscription_cost, redemption_cost) VALUES(%s, %s, %s, %s, %s, %s)"
    performance_sql = "REPLACE INTO fnz_fund_performance_history(isin, pricing_date, currency, price, ytd, 3m, 1y, 2y, 3y, 5y) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    performance_sql_2 = "REPLACE INTO fnz_fund_performance(isin, pricing_date, currency, price, ytd, 3m, 1y, 2y, 3y, 5y) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    non_tradable_sql = 'UPDATE mutual_fund set buyable = 0 where product_id = %s'

    all_funds = get_fnz_funds()
    num_of_funds = len(all_funds)
    logger.info('# of funds fetched from FNZ: ' + str(num_of_funds))

    fund_name_stmt = []
    mutual_fund_stmt = []
    fund_charges_stmt = []
    performance_stmt = []
    non_tradable_funds_stmt = []

    for row in all_funds:
        sellable = row['Sellable']
        if sellable != True:
            product_id = row.get('ProductId', '')
            non_tradable_funds_stmt.append((product_id))
            continue

        isin = row['FundIdentifiers'].get('Isin','')

        if isin in isin_map:
            branding = isin_map[isin]['BrandingName']
            mStarId = isin_map[isin]['MStarID']
            name = isin_map[isin]['FundName']
            name_cn = isin_map[isin]['FundName_CN']
            strategy = isin_map[isin]['InvestmentStrategy']
            strategy_cn = '' if isin_map[isin]['InvestmentStrategy_CHN'] == 'NULL' else isin_map[isin]['InvestmentStrategy_CHN']
            strategy_tw = '' if isin_map[isin]['InvestmentStrategy_TCHN'] == 'NULL' else isin_map[isin]['InvestmentStrategy_TCHN']
            mstar_category = isin_map[isin]['CategoryCode']
            mstar_broad_category_group_id = isin_map[isin]['BroadCategoryGroupID']
        else:
            if isin is not None and row['Sellable']:
                log_msg = 'missing isin [%s], buyable [%s] description [%s] in morningStar' % (isin, row['Sellable'], row['Description'])
                logger.info(log_msg)
            continue

        pricing_date = row['Price']['PricingDate']
        price = "{0:.2f}".format(row['Price']['Value'].get('Value', 0.0))
        fnz_code = row['FundIdentifiers'].get('ProductCode','')
        #name = row.get('Name','')
        product_id = row.get('ProductId','')
        logger.info('Processing product with id %s' % product_id)
        inception_date = row.get('LaunchDate','')
        fund_size = row.get('FundSize', 0.0)
        #strategy = row.get('Description','')
        asset_class = row.get('AssetClass','')
        sub_asset_class = row.get('AssetSubClass','')
        buyable = row.get('Sellable','')
        fund_manager_detail = row.get('FundManagerDetails', None)
        if isinstance(fund_manager_detail, dict):
            company = row['FundManagerDetails'].get('CompanyName', '')
        else:
            company = ''

        primary_index_obj = row.get('PrimaryIndex', None)
        if isinstance(primary_index_obj, dict):
            primary_index = row['PrimaryIndex'].get('Name', '')
        else:
            primary_index = ''

        domicile = row.get('Domicile','')
        currency = row.get('Currency','')
        div_type = row.get('DividendReinvestment','')
        min_initial_inv_amt = str(row.get('MinInitialInvestmentAmount', ''))

        charges = row.get('Charges', None)
        if isinstance(charges, dict):
            initial_charge = str(row['Charges']['InitialCharge'].get('Value', ''))
            annual_management_charge = str(row['Charges']['AnualManagementCharge'].get('Value', ''))
            subscription_charge = str(row['Charges']['SubScriptionCost'].get('Value', ''))
            redemption_charge = str(row['Charges']['RedemptionCost'].get('Value', ''))
        else:
            initial_charge = ''
            annual_management_charge = ''
            subscription_charge = ''
            redemption_charge = ''

        #Performance
        ytd = row['HistoricalPerformance'].get('YearToDate', 0.0)
        three_m = row['HistoricalPerformance'].get('ThreeMonth', 0.0)
        one_y = row['HistoricalPerformance'].get('OneYear', 0.0)
        two_y = row['HistoricalPerformance'].get('TwoYear', 0.0)
        three_y = row['HistoricalPerformance'].get('ThreeYear', 0.0)
        five_y = row['HistoricalPerformance'].get('FiveYear', 0.0)

        ytd = '' if ytd is None else "{0:.5f}".format(ytd)
        three_m = '' if three_m is None else "{0:.5f}".format(three_m)
        one_y = '' if one_y is None else "{0:.5f}".format(one_y)
        two_y = '' if two_y is None else "{0:.5f}".format(two_y)
        three_y = '' if three_y is None else "{0:.5f}".format(three_y)
        five_y = '' if five_y is None else "{0:.5f}".format(five_y)

        fund_name_stmt.append((mStarId, name, name_cn))
        mutual_fund_stmt.append((name, product_id, isin, fnz_code, currency, inception_date, fund_size,
                                 strategy, strategy_cn, strategy_tw, domicile, div_type, asset_class, sub_asset_class,
                                 branding, company, primary_index, mStarId, mstar_category, mstar_broad_category_group_id, buyable))
        fund_charges_stmt.append((isin, min_initial_inv_amt, initial_charge, annual_management_charge, subscription_charge, redemption_charge))
        performance_stmt.append((isin, pricing_date, currency, price, ytd, three_m, one_y, two_y, three_y, five_y))

    for product_id in non_tradable_funds_stmt:
        log_msg = 'Skipping non tradable product id: %s' % product_id
        logger.info(log_msg)

    logger.info('Executing insert sql')
    cursor.executemany(fund_name_sql, fund_name_stmt)
    cursor.executemany(mf_sql, mutual_fund_stmt)
    cursor.executemany(charge_sql, fund_charges_stmt)
    cursor.executemany(performance_sql, performance_stmt)
    cursor.executemany(performance_sql_2, performance_stmt)
    cursor.executemany(non_tradable_sql, non_tradable_funds_stmt)

    logger.info('Commiting data into database')
    conn.commit()
    conn.close()

def extract_brandings(isin_map):
    all_funds = list(isin_map.values())
    # remove duplicates
    brandings = set(fund['BrandingName'].strip() for fund in all_funds)
    # filter ''
    brandings = [brand for brand in brandings if brand.strip()]
    return brandings

def insert_fund_branding(brandings):
    logger.info('Inserting into fund_branding')
    conn = get_fund_db_conn()
    cursor = conn.cursor()

    fund_branding_sql = "INSERT INTO fund_branding values(%s, '', '') ON DUPLICATE KEY UPDATE name = %s"
    fund_branding_stmt = []

    for branding in brandings:
        fund_branding_stmt.append((branding, branding))

    cursor.executemany(fund_branding_sql, fund_branding_stmt)
    logger.info('Commiting data into database')
    conn.commit()
    conn.close()

def read_fnz_fund_list():
    isin_map = read_from_ms_database()
    brandings = extract_brandings(isin_map)
    insert_fund_branding(brandings)
    insert_mutual_funds(isin_map)

if __name__ == '__main__':
    read_fnz_fund_list()
    logger.info('Finished updating database using FNZ api')