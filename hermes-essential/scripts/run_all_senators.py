
import os, json, logging, datetime, requests, subprocess, sys

SECTORS = ['akademisi', 'bisnis', 'komunitas', 'pemerintah', 'media']
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8673939697:AAEFPs2G-xhbTl8eJ7hnPk5ezc4PZeLhSrU')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '5807834405')
ORCHESTRATOR_URL = os.getenv('ORCHESTRATOR_URL', 'http://localhost:8000')
API_KEY = os.getenv('API_KEY', 'hermes-orchestrator-key-2026')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('Senator-All')

RESEARCH_TOPICS = {
    'akademisi': ['Tren penelitian AI terbaru 2026', 'Publikasi jurnal internasional terkait teknologi', 'Kolaborasi akademik global bidang komputasi'],
    'bisnis': ['Analisis pasar teknologi 2026', 'Startup unicorn dan valuasi terkini', 'Tren investasi digital global'],
    'komunitas': ['Isu sosial masyarakat digital', 'Pergerakan komunitas open source', 'Adopsi teknologi di kalangan masyarakat'],
    'pemerintah': ['Regulasi AI dan tata kelola data', 'Kebijakan transformasi digital nasional', 'Kerja sama pemerintah swasta teknologi'],
    'media': ['Berita teknologi trending hari ini', 'Liputan media sosial tentang AI', 'Narasi publik tentang transformasi digital']
}

def gather_research(sector):
    topics = RESEARCH_TOPICS.get(sector, [])
    findings = []
    for topic in topics:
        finding = {
            'topic': topic,
            'summary': 'Penemuan riset tentang {} - {}'.format(topic, datetime.datetime.now().isoformat()),
            'source': 'Sumber simulasi untuk ' + sector,
            'timestamp': datetime.datetime.now().isoformat(),
            'sector': sector,
            'engagement': {'shares': 0, 'retweets': 0, 'views': 0}
        }
        findings.append(finding)
    return findings

def store_to_skp(findings, sector):
    url = ORCHESTRATOR_URL + '/api/knowledge'
    headers = {'X-API-Key': API_KEY, 'Content-Type': 'application/json'}
    success = 0
    for f in findings:
        payload = {
            'title': '[{}] {}'.format(sector.upper(), f['topic']),
            'content': json.dumps(f, ensure_ascii=False),
            'category': 'research',
            'source_agent_id': 'senator-{}'.format(sector),
            'source_agent_name': 'Senator {}'.format(sector.capitalize()),
            'tags': [sector, 'pentahelix', 'senator', 'raw'],
            'priority': 7
        }
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=10)
            if resp.status_code in (200, 201):
                logger.info('Stored to SKP: ' + f['topic'])
                success += 1
            else:
                logger.warning('SKP store failed: {}'.format(resp.status_code))
        except Exception as e:
            logger.error('Error storing to SKP: ' + str(e))
    return success

def append_to_local_file(findings, sector):
    local_file = '/root/senator-pentahelix/data/research_latest.json'
    os.makedirs(os.path.dirname(local_file), exist_ok=True)
    if os.path.exists(local_file):
        with open(local_file, 'r') as fp:
            try:
                data = json.load(fp)
            except:
                data = []
    else:
        data = []
    for f in findings:
        f['_sector'] = sector
        data.append(f)
    with open(local_file, 'w') as fp:
        json.dump(data, fp, ensure_ascii=False, indent=2)
    logger.info('Appended to local file: ' + local_file)

def main():
    logger.info('Starting research for all sectors...')
    for sector in SECTORS:
        logger.info('Sector: ' + sector)
        findings = gather_research(sector)
        logger.info('Gathered {} findings.'.format(len(findings)))
        success = store_to_skp(findings, sector)
        logger.info('Stored {} entries to SKP.'.format(success))
        append_to_local_file(findings, sector)
    logger.info('All sectors done.')

if __name__ == '__main__':
    main()
