'''Function:
    Implementation of MusicdlGUI
Author:
    Zhenchao Jin
WeChat Official Account (微信公众号):
    Charles的皮卡丘
'''

'''
    musicdlgui 汉化版 2.0 更新内容如下：
    1.允许用户自定义下载路径并保存路径设置
    2.优化代码结构
    3.修复已知问题
'''
import os
import sys
import json
import requests
from PyQt5 import *
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from musicdl import musicdl
from PyQt5.QtWidgets import *
from musicdl.modules.utils.misc import touchdir, sanitize_filepath


'''MusicdlGUI'''
class MusicdlGUI(QWidget):
    def __init__(self):
        super(MusicdlGUI, self).__init__()
        # initialize
        self.setWindowTitle('MusicdlGUI —— Charles的皮卡丘')
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), 'icon.ico')))
        self.setFixedSize(900, 520)
        self.initialize()
        # 配置文件管理
        self.config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config = self.read_config()
        # 下载路径
        self.download_path = self.config.get('download_path', os.path.dirname(__file__))
        # search sources
        self.src_names = ['QQ音乐', '酷我音乐', '咪咕音乐', '千千音乐', '酷狗音乐', '网易云音乐']
        self.src_map = {
            'QQ音乐': 'QQMusicClient',
            '酷我音乐': 'KuwoMusicClient',
            '咪咕音乐': 'MiguMusicClient',
            '千千音乐': 'QianqianMusicClient',
            '酷狗音乐': 'KugouMusicClient',
            '网易云音乐': 'NeteaseMusicClient'
        }
        self.label_src = QLabel('搜索引擎:')
        self.check_boxes = []
        for src in self.src_names:
            cb = QCheckBox(src, self)
            cb.setCheckState(QtCore.Qt.Checked)
            self.check_boxes.append(cb)
        # input boxes
        self.label_keyword = QLabel('关键词:')
        self.lineedit_keyword = QLineEdit('')
        self.button_keyword = QPushButton('搜索')
        # 下载路径选择
        self.label_download_path = QLabel('下载路径:')
        self.lineedit_download_path = QLineEdit(self.download_path)
        self.button_browse = QPushButton('浏览')
        # search results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(['序号', '歌手', '歌名', '文件大小', '时长', '专辑', '来源'])
        self.results_table.horizontalHeader().setStyleSheet("QHeaderView::section{background:skyblue;color:black;}")
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        # mouse click menu
        self.context_menu = QMenu(self)
        self.action_download = self.context_menu.addAction('下载')
        # progress bar
        self.bar_download = QProgressBar(self)
        self.label_download = QLabel('下载进度:')
        # grid
        grid = QGridLayout()
        grid.addWidget(self.label_src, 0, 0, 1, 1)
        for idx, cb in enumerate(self.check_boxes): grid.addWidget(cb, 0, idx+1, 1, 1)
        grid.addWidget(self.label_keyword, 1, 0, 1, 1)
        grid.addWidget(self.lineedit_keyword, 1, 1, 1, len(self.src_names)-1)
        grid.addWidget(self.button_keyword, 1, len(self.src_names), 1, 1)
        grid.addWidget(self.label_download_path, 2, 0, 1, 1)
        grid.addWidget(self.lineedit_download_path, 2, 1, 1, len(self.src_names)-1)
        grid.addWidget(self.button_browse, 2, len(self.src_names), 1, 1)
        grid.addWidget(self.label_download, 3, 0, 1, 1)
        grid.addWidget(self.bar_download, 3, 1, 1, len(self.src_names))
        grid.addWidget(self.results_table, 4, 0, len(self.src_names), len(self.src_names)+1)
        self.grid = grid
        self.setLayout(grid)
        # connect
        self.button_keyword.clicked.connect(self.search)
        self.results_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.mouseclick)
        self.action_download.triggered.connect(self.download)
        self.button_browse.clicked.connect(self.browse_download_path)
    '''initialize'''
    def initialize(self):
        self.search_results = {}
        self.music_records = {}
        self.selected_music_idx = -10000
        self.music_client = None
    '''mouseclick'''
    def mouseclick(self):
        self.context_menu.move(QCursor().pos())
        self.context_menu.show()
    '''download'''
    def download(self):
        self.selected_music_idx = str(self.results_table.selectedItems()[0].row())
        song_info = self.music_records.get(self.selected_music_idx)
        # 使用用户选择的下载路径
        self.download_path = self.lineedit_download_path.text()
        # 确保下载路径存在
        if not os.path.exists(self.download_path):
            os.makedirs(self.download_path, exist_ok=True)
        with requests.get(song_info['download_url'], headers=self.music_client.music_clients[song_info['source']].default_download_headers, stream=True, verify=False) as resp:
            if resp.status_code == 200:
                total_size, chunk_size, download_size = int(resp.headers['content-length']), 1024, 0
                # 直接使用用户选择的路径保存文件
                download_music_file_path = sanitize_filepath(os.path.join(self.download_path, song_info['song_name']+'.'+song_info['ext']))
                with open(download_music_file_path, 'wb') as fp:
                    for chunk in resp.iter_content(chunk_size=chunk_size):
                        if not chunk: continue
                        fp.write(chunk)
                        download_size += len(chunk)
                        self.bar_download.setValue(int(download_size / total_size * 100))
        QMessageBox().information(self, '下载成功', f"已将 {song_info['song_name']} 下载到 {download_music_file_path}")
        self.bar_download.setValue(0)
        # 保存配置
        self.config['download_path'] = self.download_path
        self.write_config()
    '''search'''
    def search(self):
        self.initialize()
        # selected music sources
        music_sources = []
        for cb in self.check_boxes:
            if cb.isChecked():
                music_sources.append(self.src_map[cb.text()])
        # keyword
        keyword = self.lineedit_keyword.text()
        # search
        self.music_client = musicdl.MusicClient(music_sources=music_sources)
        self.search_results = self.music_client.search(keyword=keyword)
        # showing
        count, row = 0, 0
        for per_source_search_results in self.search_results.values():
            count += len(per_source_search_results)
        self.results_table.setRowCount(count)
        for _, (_, per_source_search_results) in enumerate(self.search_results.items()):
            for _, per_source_search_result in enumerate(per_source_search_results):
                source_name = next(key for key, value in self.src_map.items() if value == per_source_search_result['source'])
                for column, item in enumerate([str(row), per_source_search_result['singers'], per_source_search_result['song_name'], per_source_search_result['file_size'], per_source_search_result['duration'], per_source_search_result['album'], source_name]):
                    self.results_table.setItem(row, column, QTableWidgetItem(item))
                    self.results_table.item(row, column).setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.music_records.update({str(row): per_source_search_result})
                row += 1
        # return
        return self.search_results
    '''读取配置文件'''
    def read_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}
    '''写入配置文件'''
    def write_config(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception:
            pass
    '''浏览下载路径'''
    def browse_download_path(self):
        path = QFileDialog.getExistingDirectory(self, '选择下载路径', self.download_path)
        if path:
            self.download_path = path
            self.lineedit_download_path.setText(path)
            # 保存配置
            self.config['download_path'] = self.download_path
            self.write_config()


'''tests'''
if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = MusicdlGUI()
    gui.show()
    sys.exit(app.exec_())