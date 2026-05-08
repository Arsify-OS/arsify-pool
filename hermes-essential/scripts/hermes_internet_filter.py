#!/usr/bin/env python3
"""
hermes-internet filter: reads research data from local file,
filters top 3 viral per sector, sends Telegram report.
"""
import os, json, logging, datetime, requests, sys, glob

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5807834405')
DATA_DIR = '/root/senator-pentahelix/data'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('hermes-internet')

def read_latest_data():
    """Read the most recent research file."""
    pattern = os.path.join(DATA_DIR, 'research_*.json')
    files = glob.glob(pattern)
    if not files:
        logger.warning('No research data files found.')
        return []
    latest_file = max(files, key=os.path.getctime)
    logger.info('Reading from: ' + latest_file)
    with open(latest_file, 'r') as fp:
        try:
            data = json.load(fp)
            return data, latest_file
        except Exception as e:
            logger.error('Error reading file: ' + str(e))
            return [], latest_file

def filter_top3_per_sector(data):
    """Group by sector and pick top 3 by engagement (dummy)."""
    sectors = {}
    for item in data:
        sec = item.get('sector', item.get('_sector', 'unknown'))
        if sec not in sectors:
            sectors[sec] = []
        sectors[sec].append(item)
    result = {}
    for sec, items in sectors.items():
        # Sort by dummy engagement: sum of shares, retweets, views
        def engagement(item):
            eng = item.get('engagement', {})
            return sum([eng.get('shares', 0), eng.get('retweets', 0), eng.get('views', 0)])
        sorted_items = sorted(items, key=engagement, reverse=True)
        result[sec] = sorted_items[:3]
    return result

def format_telegram_message(top_data):
    """Format message according to JUKLAK."""
    now = datetime.datetime.now()
    msg = "📡 LAPORAN PENTAHELIX — 6 JAM TERAKHIR\n"
    msg += "🕐 {} WIB | {}\n\n".format(now.strftime('%H:%M'), now.strftime('%d %b %Y'))
    sector_names = {
        'akademisi': '🏛️ AKADEMISI',
        'bisnis': '💼 BISNIS',
        'komunitas': '👥 KOMUNITAS',
        'pemerintah': '🏛️ PEMERINTAH',
        'media': '📰 MEDIA'
    }
    for sec, items in top_data.items():
        display = sector_names.get(sec, sec.upper())
        msg += display + "\n"
        for i, item in enumerate(items, 1):
            topic = item.get('topic', 'No title')
            # Dummy metrics
            eng = item.get('engagement', {})
            metrics = []
            if eng.get('shares'):
                metrics.append('{} shares'.format(eng['shares']))
            if eng.get('retweets'):
                metrics.append('{} retweets'.format(eng['retweets']))
            if eng.get('views'):
                metrics.append('{} views'.format(eng['views']))
            metric_str = ', '.join(metrics) if metrics else 'N/A'
            msg += "{}. {} — {}\n".format(i, topic, metric_str)
            msg += "   🔗 [link]\n"  # placeholder
        msg += "\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    total = sum(len(v) for v in top_data.values())
    msg += "📊 {} temuan viral dari 5 sektor\n".format(total)
    msg += "💾 Data lengkap tersimpan di SKP\n"
    msg += "🏛️ Arsiparis: hermes-archivist (9124)\n"
    return msg

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning('Telegram credentials not set.')
        return False
    url = 'https://api.telegram.org/bot{}/sendMessage'.format(TELEGRAM_BOT_TOKEN)
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            logger.info('Telegram report sent.')
            return True
        else:
            logger.warning('Telegram send failed: {}'.format(resp.status_code))
    except Exception as e:
        logger.error('Error sending Telegram: ' + str(e))
    return False

def main():
    logger.info('hermes-internet filter started.')
    data, source_file = read_latest_data()
    if not data:
        logger.warning('No data to process.')
        return
    logger.info('Total items: {}'.format(len(data)))
    top_data = filter_top3_per_sector(data)
    message = format_telegram_message(top_data)
    logger.info('Sending Telegram report...')
    send_telegram(message)
    # Archive the processed file
    archive_dir = os.path.join(DATA_DIR, 'archive')
    os.makedirs(archive_dir, exist_ok=True)
    import shutil
    shutil.move(source_file, os.path.join(archive_dir, os.path.basename(source_file)))
    logger.info('Data archived.')

if __name__ == '__main__':
    main()
