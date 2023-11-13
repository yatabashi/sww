"""
ランダムなグラフの生成
グラフが連結でなければ連結グラフの集合として出力する／連結させる
Page をサーバー内に保管しておく？
    cf. Web.getHypertextFromHyperlinks
"""

from typing import Type, Union
import copy
import random

# Webページに相当する
class Page:
    def __init__(self, id: int, content: str, destinationIds: set[int]):
        self.id: int = id
        self.text: str = content
        self.destinationIds: set[int] = destinationIds
    
    # ページにハイパーリンクを追加する
    def addLink(self, *destinationIds: int):
        self.destinationIds.update(set(destinationIds))

    # ページから指定したハイパーリンクを削除する
    def deleteLink(self, *destinationIds: int):
        for id in destinationIds:
            self.destinationIds.discard(id)

# （DNS+）サーバに相当する
class Server:
    def __init__(self, pages: set[Type[Page]] = {}):
        self.record: dict[int, Type[Page]] = {page.id: page for page in pages}

    # 指定の id を持つページを返す
    def getPage(self, id: int) -> Union[Page, None]:
        return self.record.get(id)
    
    # ページをサーバに追加する
    def addPage(self, *pages: Type[Page]):
        self.record.update({(page.id, page) for page in pages})
    
    # 指定したページをサーバから削除する
    def deletePage(self, *ids: int):
        for id in ids:
            self.record.pop(id, None)

    # ハイパーリンクの集合からページの一覧を取得する
    @classmethod
    def getPagesFromHyperlinks(cls, hyperlinks: set[tuple[int, int]]):
        # 行列を辞書に変換する
        d: dict[int, Page] = {}

        for hyperlink in hyperlinks:
            if hyperlink[0] in d:
                d[hyperlink[0]].destinationIds.add(hyperlink[1])
            else:
                d[hyperlink[0]] = Page(hyperlink[0], "", {hyperlink[1]})
                
        return d.values()


# WWW に相当するハイパーテキスト
class Web:
    def __init__(self, server: Server, initialPageId: int):
        self.server: Server = server  # ハイパーテキストを構築するページ群が置かれたサーバ
        self.initialPageId = initialPageId  # 既知として与えられる周回の起点となるページ
        self.hypertext: dict[int, set[int]] = dict()
        self.reconstruct(initialPageId)

    # ハイパーテキストを構築する
    def initialise(self, locationId: int):
        # ページが周回済みだった場合
        if locationId in self.hypertext:
            return
        
        # ページが存在しなかった（初めからないか、削除されている）場合
        location = self.server.getPage(locationId)
        if location is None:
            return

        # ハイパーリンクを保存する
        self.hypertext[locationId] = copy.copy(location.destinationIds)

        # リンク先の各ページを起点にハイパーテキストを構築する
        for i in location.destinationIds:
            self.initialise(i)
    
    # ハイパーテキストを初期化して構築する
    def reconstruct(self, initialPageId: int):
        self.hypertext.clear()
        self.initialise(initialPageId)

    # ハイパーテキストを更新する
    def crawl(self):
        gonePageIds = set()
        appearedPageIds = set()

        # 保存されているハイパーテキストにあるページを順に確認する
        for locationId in self.hypertext:
            # ページが削除されていれば記録する
            if self.server.getPage(locationId) is None:
                gonePageIds.add(locationId)
                continue
            
            # ページ内のハイパーリンクを新旧比較する
            oldDestinationIds = self.hypertext[locationId]
            newDestinationIds = self.server.getPage(locationId).destinationIds
            if oldDestinationIds != newDestinationIds:
                # ハイパーリンクを上書き保存する
                self.hypertext[locationId] = copy.copy(newDestinationIds)
                
                # 新たなリンク先があれば、未周回のページのみ記録する
                appearedPageIds |= (newDestinationIds - oldDestinationIds) - self.hypertext.keys()
        
        # 削除されたページをハイパーテキストから除外する
        for id in gonePageIds:
            self.hypertext.pop(id)

        # 新たに現れたページを起点にハイパーテキストを構築する
        for id in appearedPageIds:
            self.initialise(id)
    
    # ハイパーテキストの構造を返す
    def getHypertext(self) -> dict[int, set[int]]:
        return self.hypertext
    
    # ハイパーテキストの構造をソートして返す
    def getSortedHypertext(self) -> dict[int, set[int]]:
        return dict(sorted(self.hypertext.items(), key=(lambda x: x[0])))

    # ハイパーテキスト内の全リンクを返す
    def getHyperlinks(self) -> set[tuple[int, int]]:
        s = set()

        # ハイパーリンクをタプルに変換する
        for (startId, endIds) in self.hypertext.items():
            s.update({(startId, endId) for endId in endIds})
                
        return s
    
    # ハイパーテキスト内の全リンクをソートして返す
    def getSortedHyperlinks(self) -> set[tuple[int, int]]:
        return sorted(list(self.getHyperlinks()))
    
    # ハイパーリンクの集合からハイパーテキストの構造を取得する
    # 新たに Page を生成している←もとの Server 内に Page があるならそれを利用すべき？
    # content が消える問題もある
    @classmethod
    def getHypertextFromHyperlinks(cls, hyperlinks: set[tuple[int, int]]):
        # 行列を辞書に変換する
        d: dict[int, set[int]] = {}

        for hyperlink in hyperlinks:
            if hyperlink[0] in d:
                d[hyperlink[0]].add(hyperlink[1])
            else:
                d[hyperlink[0]] = {hyperlink[1]}
                
        return d

    # ハイパーリンクを辿って目的のページに辿り着くことを目指すゲーム
    def explore(self, treasure: int = None):
        # 与えられた str が int 形式に変換可能かを返す
        def isint(i: str):
            try:
                int(i)
            except:
                return False
            else:
                return True

        # ハイパーリンクを辿る
        def proceed(locationId: int, path: list[str] = []):
            # 現在地が目的地だった場合
            if locationId == treasure:
                print("→".join(path)+("→" if path else "")+str(locationId))
                print(f"You reached page {treasure}!")
            # 現在地に相当するページが存在しなかった場合
            elif self.server.getPage(locationId) is None:
                print(f"Page {locationId} is gone!")
                proceed(int(path[-1]), path[:-1])
            # 現在地が目的地以外のページだった場合
            else:
                print("→".join(path)+("→" if path else "")+str(locationId)+"→"+str(self.server.getPage(locationId).destinationIds))
                v = input(f"Go to: ")
                
                # 入力値が"quit"だった場合
                if v == "quit":
                    return 1
                # 入力値が"back"だった場合
                elif v == "back":
                    if path == []:
                        print("Can't go back. If you want to end the game, type \'quit\'.")
                        if proceed(locationId, path): return 1
                    else:
                        if proceed(int(path[-1]), path[:-1]): return 1
                # 入力値が整数として解釈できなかった場合
                elif not isint(v):
                    print(f"Invalid input")
                    if proceed(locationId, path): return 1
                # 入力値が整数として解釈される場合
                else:
                    destination = int(v)

                    # 入力されたページに現在地からアクセスできない場合
                    if destination not in self.server.getPage(locationId).destinationIds:
                        print(f"Can't move to {v}")
                        if proceed(locationId, path): return 1
                    # 入力されたページに現在地からアクセスできる場合
                    else:
                        if proceed(destination, path+[str(locationId)]): return 1

        # 目的地が与えられていない場合はランダムに決定する
        # 到達不能なページも候補にある
        # reconstruct するべきか？
        if treasure is None:
            treasure = random.choice(list(self.hypertext.keys() - {self.initialPageId}))
        
        print(f"Search for page {treasure}!")
        proceed(self.initialPageId)
    
    # リンクをランダムに選択して移動していくロボット
    def randomwalk(self, locationId: int = None, destinationId: int = None, maxStep: int = None, path: list[str] = []):
        if locationId is None: locationId = self.initialPageId

        print(("→" if path else "")+str(locationId), end="")
        # 現在地が目的地だった場合
        if locationId == destinationId:
            print(".")
            return
        # 歩数の上限に達した場合
        elif maxStep is not None and maxStep < 1:
            print("]")
            return
        # 現在地に相当するページが存在しなかった場合
        elif self.server.getPage(locationId) is None:
            print("/")
            return
        # 現在地が目的地以外のページだった場合
        else:
            choices = self.server.getPage(locationId).destinationIds
            self.randomwalk(random.choice(list(choices)), destinationId, (None if maxStep is None else maxStep-1), path+[str(locationId)])
    
    def isConnected(self):
        def getMember(s: set):
            for m in s:
                return m

        registeredPageIds = self.hypertext.keys()
        visitedPageIds = set()
        stack = []

        startPageId = getMember(registeredPageIds)
        visitedPageIds.add(startPageId)
        stack.append(startPageId)

        while stack:
            pageId = stack.pop(-1)

            if self.server.getPage(pageId) is None:
                continue

            for destinationId in self.server.getPage(pageId).destinationIds:
                if destinationId not in visitedPageIds:
                    visitedPageIds.add(destinationId)
                    stack.append(destinationId)
        
        return not bool(registeredPageIds - visitedPageIds)

if __name__ == "__main__":
    """
        0 
      ↙︎ ⇅
  ⇨ 1 → 2 → 8
    ↓ ↗︎ ↑
    3 → 4 ← 5 ⊃
      ↖︎ ↓ ↗︎ ↑
        7   6
    """

    page0 = Page(0, "zero", {1, 2})
    page1 = Page(1, "un", {2, 3})
    page2 = Page(2, "deux", {0, 8})
    page3 = Page(3, "trois", {2, 4})
    page4 = Page(4, "quatre", {2, 7})
    page5 = Page(5, "cinq", {4, 5})
    page6 = Page(6, "six", {5})
    page7 = Page(7, "set", {3, 5})
    page8 = Page(8, "huit", set())
    server = Server({page0, page1, page2, page3, page4, page5, page6, page7, page8})
    web = Web(server, 1)
    print(web.getSortedHypertext())
    print(web.isConnected(), "but", server.record.keys() - web.getHypertext().keys(), "are missing")

    """
         
        ↑
    1 → 2   8
    ↓ ↗︎ 
    3 → 4 ← 5 ⊃
      ↖︎ ↓ ↗︎ ↑
        7 → 6
            ↑
            9
    """

    server.deletePage(0)
    page4.deleteLink(2)
    page2.deleteLink(8)
    page7.addLink(6)
    page9 = Page(9, "dix", {6})
    server.addPage(page9)
    web.crawl()
    print(web.getSortedHypertext())
    print(web.isConnected(), "but", server.record.keys() - web.getHypertext().keys(), "are missing")

    """
         
        ↑
    1 → 2   8
    ↓ ↗︎ 
    3 → 4 ← 5 ⊃
    ↑ ↖︎ ↓ ↗︎ ↑
    ↑ ← 7 → 6
            ↑
            9 ⇦
    """
    
    web.reconstruct(9)
    print(web.getSortedHypertext())
    print(web.isConnected(), "but", server.record.keys() - web.getHypertext().keys(), "are missing")

    hls = web.getHyperlinks()
    print(hls)
    hlsdash = Server.getPagesFromHyperlinks(hls)
    print(Web(Server(hlsdash), 9).getHypertext())

    # web.explore()

    for _ in range(5):
        web.randomwalk(9, 3, 9)
