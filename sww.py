"""
makeRandomPages ← 一旦無視？

強連結にする

強連結成分分解の非再帰化
    https://qiita.com/KowerKoint/items/870ea9ef7a39f3fe4ce3

Page をサーバー内に保管しておく？
    cf. Web.getHypertextFromHyperlinks

ランダムなグラフの生成→数字の重複を避けるために Page の保存の処置の後
    あたらしく server を作成するなら関係ないのでは？
"""
"""
強連結成分分解：
    https://manabitimes.jp/math/1250
    https://hkawabata.github.io/technical-note/note/Algorithm/graph/scc.html

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
        self.hypertext: dict[int, set[int]] = dict() # ハイパーテキストを隣接リストとして保持する
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
        self.initialPageId = initialPageId
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
    def makeHypertextFromHyperlinks(cls, hyperlinks: set[tuple[int, int]]):
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
    
    # ハイパーテキストを強連結成分（Strongly Connected Components）分解する
    # 有向グラフの強連結成分とは、その部分木であって任意の2頂点間に双方向に有向路がある（＝強連結である）ものを言う
    # Kosaraju のアルゴリズムに相当する
    def getSCCs(self, printsDetails: bool = False) -> set[set[int]]:
        def getMember(s: set) -> any:
            for m in s:
                return m
        
        # ページをラベリングする
        hypertext = self.getHypertext()
        ## ラベリング関数の定義
        ## 削除されたページもラベリングされる
        def label(n: int = 0, pageIdToLabel: dict[int, int] = {}, visitedPageIds: set[int] = set()):
            # 片道のラベリング関数の定義
            # 始点に戻ってきたら終了し、未周回のページを残しうる
            def label_oneway(locationId: int, n: int = 0) -> int:
                # 周回済だった場合（処理済であるか、のちに処理されるので無視）
                if locationId in visitedPageIds:
                    return n
                # リンク先がない場合
                elif not hypertext.get(locationId):
                    visitedPageIds.add(locationId) # 周回済にする
                    pageIdToLabel[locationId] = n  # ラベリングする
                    n += 1                         # 次のラベルの値をこのページのラベル + 1 にする
                    return n                       # 次に付けられるべきラベルの値を返す
                # リンク先がある場合
                else:
                    visitedPageIds.add(locationId)
                    # 各リンク先において片道のラベリングを行う
                    for destinaionId in hypertext.get(locationId):
                        n = label_oneway(destinaionId, n) # 次のラベルの値を与え、再帰する
                    pageIdToLabel[locationId] = n
                    n += 1
                    return n

            # ラベリングされていないページがあるならば
            if leftPageIds := hypertext.keys() - visitedPageIds:
                # 適当なページから片道のラベリングを行う
                n = label_oneway(getMember(leftPageIds), n)

                # 再帰的にラベリングを続ける
                return label(n, pageIdToLabel, visitedPageIds)
            # すべてラベリングされているならば
            else:
                return pageIdToLabel
        
        ## ラベリングの実行
        pageIdTolabel = label()
        labelToPageId = {label: pageId for (pageId, label) in pageIdTolabel.items()}

        # ハイパーテキストの転置グラフ*を取得する
        # *すべてのエッジ（リンク）を反転させたものを言う
        def getTransposeHypertext():
            hyperlinks = self.getHyperlinks()
            transpose = {hyperlink[::-1] for hyperlink in hyperlinks}
            return Web.makeHypertextFromHyperlinks(transpose)

        ## 取得の実行
        transposeHypertext = getTransposeHypertext()

        # decompose: 辿り直して分解
        def getComponents(foundComponents: set[frozenset[int]] = set(), visitedPageIds: set[int] = set()) -> set[frozenset[int]]:
            # 強連結成分を一つ取得する関数の定義
            # あるページから転置グラフを辿って到達可能な（自身をリンク先としている）ページの集合を返す
            def getOneComponent(locationId: int) -> frozenset[int]:
                # 周回済だった場合
                if locationId in visitedPageIds:
                    if printsDetails: print(locationId, "is visited; return")
                    return frozenset()
                # リンク先がない場合
                elif not transposeHypertext.get(locationId):
                    if printsDetails: print(locationId, "has no links; return")
                    visitedPageIds.add(locationId) # 周回済にする
                    return frozenset({locationId})
                # リンク先がある場合
                else:
                    if printsDetails: print(locationId, "has link;")
                    visitedPageIds.add(locationId)
                    rv = frozenset({locationId})
                    for destinaionId in transposeHypertext.get(locationId):
                        rv |= getOneComponent(destinaionId)
                        if printsDetails: print("component is updated:", rv)
                    return rv

            # 未周回のページがあるならば
            if transposeHypertext.keys() - visitedPageIds:
                nonlocal pageIdTolabel
                nonlocal labelToPageId

                if printsDetails: print("labelling:", labelToPageId)
                if printsDetails: print("pageIdWithMaxLabel:", labelToPageId[max(labelToPageId.keys())])

                # ラベルが最大のページから強連結成分を取得する
                component = getOneComponent(labelToPageId[max(labelToPageId.keys())])

                # 分解された成分に割り当てられたラベリングの削除
                # 最大のラベルを取得しやすくする
                pageIdTolabel = {pageId: label for (pageId, label) in pageIdTolabel.items() if pageId not in component}
                labelToPageId = {label: pageId for (pageId, label) in pageIdTolabel.items()}
                if printsDetails: print("component:", component)

                # 分解された成分を強連結成分の集合に追加する
                foundComponents.add(component)

                # 再帰的にラベリングを続ける
                return getComponents(foundComponents, visitedPageIds)
            # すべてラベリングされているならば
            else:
                return foundComponents
            
        return getComponents()

    def isStronglyConnected(self):
        return len(self.getSCCs())




if __name__ == "__main__":
    """
        0   8 ← 10
      ↙︎ ⇅     ↘︎ ↑
  ⇨ 1 → 2       9 → 11
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ⇄ 12
      ↖︎ ↓ ↗︎ ↑
        7  (6)

        0   8 ← 10
      ↙︎ ⇅     ↘︎ ↑
  ⇨ 1 → 2       9 → 11
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ⇄ 12
      ↖︎ ↓ ↗︎ ↑
        7  (g)
    """

    page0 = Page(0, "a", {1, 2})
    page1 = Page(1, "b", {2, 3})
    page2 = Page(2, "c", {0})
    page3 = Page(3, "d", {2, 4})
    page4 = Page(4, "e", {2, 7})
    page5 = Page(5, "f", {4, 5, 12})
    page6 = Page(6, "g", {5})
    page7 = Page(7, "h", {3, 5})
    page8 = Page(8, "i", {9})
    page9 = Page(9, "j", {10, 11})
    page10 = Page(10, "k", {8})
    page11 = Page(11, "l", set())
    page12 = Page(12, "m", {5, 9})
    server = Server({page0, page1, page2, page3, page4, page5, page6, page7, page8, page9, page10, page11, page12})
    web = Web(server, 1)
    print("hypertext:", web.getSortedHypertext())
    print(web.isStronglyConnected(), "SCCs")
    print("\n——————————\n")

    # web.tp(); 

    """
       ~a~  i ← k
        ↑     ↘︎ ↑
    b → c       j → l
    ↓ ↗︎ ↑   ∩   ↑
    d → e ← f ← m
      ↖︎ ↓ ↗︎ ↑
        h → g
            ↑
           (n)

       ~0~  11← 8
        ↑     ↖︎ ↑
    7 → 1       10→ 9
    ↓ ↗︎ ↑   ∩   ↑
    6 → 5 ← 2 ← 12
      ↖︎ ↓ ↗︎ ↑
        4 → 3
            ↑
           (n)
    """

    server.deletePage(0)
    page5.deleteLink(12)
    page7.addLink(6)
    page13 = Page(13, "n", {6})
    server.addPage(page13)
    web.crawl()
    print("hypertext:", web.getSortedHypertext())
    print(web.isStronglyConnected(), "SCCs")
    print("\n——————————\n")

    """
       ~0~
        ↑
        2
      ↗︎ ↑   ∩
    3 → 4 ← 5
      ↖︎ ↓ ↗︎ ↑
        7 → 6
            ↑
            13⇦

       ~0~
        ↑
        1
      ↗︎ ↑   ∩
    2 → 4 ← 5
      ↖︎ ↓ ↗︎ ↑
        3 → 6
            ↑
            7 ⇦
    """
    
    web.reconstruct(13)
    print("hypertext:", web.getSortedHypertext())
    print(web.isStronglyConnected(), "SCCs")
    print("\n——————————\n")

    # web.explore()

    # for _ in range(5):
    #     web.randomwalk(9, 3, 9)

    """
    0 → 1 → 2 → 4
        ↑ ↙︎
        3
    """
    pagea = Page(20, "", {21})
    pageb = Page(21, "", {22})
    pagec = Page(22, "", {23, 24})
    paged = Page(23, "", {21})
    pagee = Page(24, "", {})
    servera = Server({pagea, pageb, pagec, paged, pagee})
    weba = Web(servera, 20)
    print("hypertext:", weba.getSortedHypertext())
    print(web.isStronglyConnected(), "SCCs")
    print("\n——————————\n")

    