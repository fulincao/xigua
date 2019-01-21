from selenium import webdriver
import requests
from selenium.webdriver.chrome.options import Options
from pymongo import MongoClient
import threading
import os
import re
import time

base = '/data4/ian/xigua_video/'

base_url = 'https://www.ixigua.com/api/pc/feed/?category={0}&utm_source=toutiao'
host = 'https://www.ixigua.com'

kinds = ['游戏','科技','生活', '时尚', '影视', '农人','美食']

en_kinds = ['subv_xg_game', 'subv_video_tech', 'subv_xg_life', 'subv_video_fashion',
	'subv_xg_movie', 'subv_video_agriculture', 'subv_video_food'
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36', 'Cookie':'UM_distinctid=167dfad01be59d-0673a3199f0172-b781636-e1000-167dfad01bf410; _ga=GA1.2.1135044605.1545645917; WEATHER_CITY=%E5%8C%97%E4%BA%AC; _gid=GA1.2.1274313545.1545806730; CNZZDATA1262382642=178129078-1545640954-https%253A%252F%252Fwww.baidu.com%252F%7C1545886378; tt_webid=6639546329273468429' }

times = 1


def download_video(url, vid, kind, title, author):
	if 'http:' not in url:
		url = 'http:' + url
	video = dict()
	video['download_url'] = url
	video['_id'] = vid
	video['kind'] = kind
	video['title'] = title
	video['author'] = author
	video['local_url'] = base + kind + '/' + title + '.mp4'
	time.sleep(2)
	resp = requests.get(url, headers = headers)
	f = open(video['local_url'], 'wb')
	for chunk in resp.iter_content(10000):
		f.write(chunk)
	f.close()
	collection.insert(video)
	print(video, 'finish....')


def mkdirs_video():
	for kind in kinds:
		path = base + kind
		if not os.path.isdir(path):
			os.makedirs(path)


def get_download_url(source_url):
	time.sleep(0.5)
	browser.get(source_url)
	browser.refresh()
	time.sleep(0.5)
	html = browser.page_source
	download_url = re.findall('<video class.*?src="(.*?)".*?>', html)[0]
	print(download_url)
	return download_url


def main():
	source_id = set()
	for i in range(len(en_kinds)):
		time.sleep(1)
		source_url = base_url.format(en_kinds[i])
		resp = requests.get(source_url, headers = headers)
		if resp.status_code != 200:
			continue
		js = resp.json()
		if js['message'] != 'success':
			continue		
		data = js['data']
		for item in data:
			try:
				vid = item['video_id']
				if vid in source_id:
					continue
				tag = item['tag_url']
				if tag != 'video':
					continue		
				title = item['title']
				kind = kinds[i]
				author = item['source']
				source_url = host + item['source_url']
				download_url = get_download_url(source_url)
				t = threading.Thread(target=download_video,args=(download_url, vid, kind, title, author))
				t.start()
				source_id.add(vid)
			except Exception as e:
				print(e)
				time.sleep(3)

if __name__ == '__main__':

	chrome_options = Options()
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument("--disable-setuid-sandbox")
	chrome_options.add_argument('--disable-dev-shm-usage')
	chrome_options.add_argument('window-size=1920x3000') #指定浏览器分辨率
	chrome_options.add_argument('--disable-gpu') #谷歌文档提到需要加上这个属性来规避bug
	chrome_options.add_argument('--hide-scrollbars') #隐藏滚动条, 应对一些特殊页面
	chrome_options.add_argument('blink-settings=imagesEnabled=false') #不加载图片, 提升速度
	chrome_options.add_argument('--headless')
	browser = webdriver.Chrome(chrome_options=chrome_options)
	
	connect = MongoClient(host='xxx', port=12345)
	db = connect['ian_video']
	collection = db['xigua']
	mkdirs_video()
	
	for i in range(times):
		main()
		print('iter ' + str(i) + ' finish')
		time.sleep(1)

	db.close()
	browser.close()
	browser.quit()


