"""
強連結成分分解の非再帰化
    https://qiita.com/KowerKoint/items/870ea9ef7a39f3fe4ce3

2ページを与え縮約したグラフを返す: O(1)
2ページを与え距離を取得する
    幅優先探索、ダイクストラ法
    https://en.wikipedia.org/wiki/Distance_(graph_theory)
    https://www.momoyama-usagi.com/entry/math-risan14
    https://qiita.com/zk_phi/items/d93f670544e4b9816ed0
    https://ja.wikipedia.org/wiki/%E3%83%80%E3%82%A4%E3%82%AF%E3%82%B9%E3%83%88%E3%83%A9%E6%B3%95
    https://dai1741.github.io/maximum-algo-2012/docs/shortest-path/
直径を取得する: O(n)
    https://take44444.github.io/Algorithm-Book/graph/tree/diameter/main.html
    https://algo-logic.info/tree-diameter/
ページを与え、それを削除し、それへのリンクも削除する: O(1)
    Server.deletePage() はリンクを削除しない
ページを与え、次数（出入それぞれ）を取得する: O(n)
    https://ja.wikipedia.org/wiki/%E6%AC%A1%E6%95%B0_(%E3%82%B0%E3%83%A9%E3%83%95%E7%90%86%E8%AB%96)
出/入次数0の孤立点を取得する: O(n)
    削除されたページをどう扱うか？
ページを与え、そこから到達可能なページを取得する
    探索するだけ
道の集合を与え、ハイパーテキストを生成する
    Server.makePagesFromHyperlinks() はエッジの集合を与える
    歩道Walk／路Trail（辺の重複なし）を与えたい
        walk から trail に変換することになりそう
        →これは別で用意したいか
    道Pathは頂点が重複しない→採用するならループは独立の要素としてあたえられなければならない
強連結度
サイクル検出
    finished でないが visited ならサイクルがある
    単に visitied だけ見た場合？
    https://drken1215.hatenablog.com/entry/2023/05/20/200517

全てのページに到達可能なページが存在するか、存在するならそれは何かを取得する関数、ひいてはそれをinit-に設定する関数が可能

ファイルシステム
"""
"""
強連結成分分解：
    https://manabitimes.jp/math/1250
    https://hkawabata.github.io/technical-note/note/Algorithm/graph/scc.html
"""
"""
ハイパーテキストは、ページをノードと、リンクをエッジとして、ループ付きの有向グラフと見做すことができる。
ここでは、単一のサーバにアップロードされ、ハイパーリンクで結ばれた（あるいは結ばれていない）ページ群を考える。
"""


from typing import Type, Union
import copy
import random

# set から要素を一つ取り出す関数
def getMember(s: set) -> any:
    for m in s:
        return m

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

# サーバに相当する
# ページを id を鍵とした辞書の形で保持し、それらを元にハイパーテキストを構築する
class Server:
    def __init__(self, pages: set[Type[Page]] = {}, initialPageId: int = None):
        self.record: dict[int, Type[Page]] = {page.id: page for page in pages}  # ページIDとページを対応付ける
        self.hypertext: dict[int, set[int]] = dict()  # ハイパーテキストを隣接リストとして保持する
        self.initialPageId: int = initialPageId if initialPageId else getMember(self.record.keys())  # クローリング周回の起点となるページ
    
    # ——— record に対する操作
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
    
    # ———ハイパーテキストの構築
    # ハイパーテキストを構築する
    def constructHypertext(self, locationId: int):
        # ページが周回済みだった場合
        if locationId in self.hypertext:
            return
        
        # ページが存在しなかった（初めからないか、削除されている）場合
        location = self.getPage(locationId)
        if location is None:
            return

        # ハイパーリンクを保存する
        self.hypertext[locationId] = copy.copy(location.destinationIds)

        # リンク先の各ページを起点にハイパーテキストを構築する
        for i in location.destinationIds:
            self.constructHypertext(i)
            
    # ハイパーテキストを構築する（非再帰）
    def constructHypertext_nonrec(self, originId: int):
        hypertext: dict[int, set[int]] = dict()
        stack = [originId]
        
        while stack:
            locationId = stack.pop()
            
            # ページが存在しないなら
            page = self.getPage(locationId)
            if page is None:
                continue
            
            # ページが未周回なら
            if locationId not in hypertext:
                hypertext[locationId] = copy.copy(page.destinationIds)
                
                for child in page.destinationIds:
                    if child not in hypertext:  # この分岐は必須ではないが、ループ回数削減に寄与する
                        stack.append(child)
        
        self.hypertext = hypertext
    
    # ハイパーテキストを初期化して構築する
    def initialiseHypertext(self, initialPageId: int = None):
        if initialPageId is not None and initialPageId != self.initialPageId:
            self.changeInitialPage(initialPageId)
        self.hypertext.clear()
        self.constructHypertext(self.initialPageId)
    
    # ハイパーテキストを更新する
    def crawlHypertext(self):
        gonePageIds = set()
        appearedPageIds = set()

        # 保存されているハイパーテキストにあるページを順に確認する
        for locationId in self.hypertext:
            # ページが削除されていれば記録する
            if self.getPage(locationId) is None:
                gonePageIds.add(locationId)
                continue
            
            # ページ内のハイパーリンクを新旧比較する
            oldDestinationIds = self.hypertext[locationId]
            newDestinationIds = self.getPage(locationId).destinationIds
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
            self.constructHypertext(id)
    
    # ハイパーテキストの構築起点を変更する
    def changeInitialPage(self, id: int):
        if id in self.record:
            self.initialPageId = id
        else:
            raise ValueError
    
    # ハイパーリンクの集合を元にページ群を（新たに）生成する
    @classmethod
    def makePagesFromHyperlinks(cls, hyperlinks: set[tuple[int, int]]) -> set[Type[Page]]:
        d: dict[int, Page] = dict()
        
        for hyperlink in hyperlinks:
            if hyperlink[0] in d:
                d[hyperlink[0]].destinationIds.add(hyperlink[1])
            else:
                d[hyperlink[0]] = Page(hyperlink[0], "", {hyperlink[1]})
                
        return d.values()
    
    # ハイパーリンクの集合からハイパーテキストを生成する
    @classmethod
    def makeHypertextFromHyperlinks(cls, hyperlinks: set[tuple[int, int]]) -> dict[int, set[int]]:
        d: dict[int, set[int]] = dict()

        for hyperlink in hyperlinks:
            if hyperlink[0] in d:
                d[hyperlink[0]].add(hyperlink[1])
            else:
                d[hyperlink[0]] = {hyperlink[1]}
                
        return d
    
    # 与えられたハイパーテキストからハイパーリンクを得る
    @classmethod
    def getHyperlinksFromHyperText(cls, hypertext: dict[int, set[int]]) -> set[tuple[int, int]]:
        s = set()

        # ハイパーリンクをタプルに変換する
        for (startId, endIds) in hypertext.items():
            s.update({(startId, endId) for endId in endIds})
                
        return s
    
    # 与えられたハイパーテキストの全てのリンクを反転させた転置グラフを生成する
    @classmethod
    def getTransposeHypertext(cls, hypertext: dict[int, set[int]]) -> dict[int, set[int]]:
        hyperlinks = Server.getHyperlinksFromHyperText(hypertext)
        transpose = {hyperlink[::-1] for hyperlink in hyperlinks}
        return Server.makeHypertextFromHyperlinks(transpose)
        
    # ———ハイパーテキストの表示
    # ハイパーテキストの構造を返す
    def getHypertext(self) -> dict[int, set[int]]:
        return self.hypertext
    
    # ハイパーテキストの構造をソートして返す
    def getSortedHypertext(self) -> dict[int, set[int]]:
        return dict(sorted(self.hypertext.items(), key=(lambda x: x[0])))
    
    # ハイパーテキスト内の全リンクを返す
    def getHyperlinks(self) -> set[tuple[int, int]]:
        return Server.getHyperlinksFromHyperText(self.hypertext)
    
    # ハイパーテキスト内の全リンクをソートして返す
    def getSortedHyperlinks(self) -> set[tuple[int, int]]:
        return sorted(list(self.getHyperlinks()))
    
    # ———ハイパーテキストの情報取得
    # 指定したページから到達可能なページのリストを取得する
    def getdescendantPageIds(self, originId: int) -> set[int]:
        descendants = set()
        stack = [originId]
        
        while stack:
            locationId = stack.pop()
            
            # ページが未周回なら
            if locationId not in descendants:
                descendants.add(locationId)
                
                page = self.getPage(locationId)
                # ページが存在しないなら
                if page is None:
                    continue
                # ページが存在するなら
                else:
                    for child in page.destinationIds:
                        if child not in descendants:  # この分岐は必須ではないが、ループ回数削減に寄与する
                            stack.append(child)
            
        return descendants
    
    # 根（リンクを辿って全てのページに到達可能なページ）を一つ取得する
    def getRoot(self):
        pageIds = self.hypertext.keys()
        stack = [getMember(pageIds)]
        
        while stack:
            locationId = stack.pop()
            
            if self.getdescendantPageIds(locationId) >= pageIds:
                return locationId
            else:
                continue
        
        return None
    
    # ———ハイパーテキストに変更を加える操作：いずれも副作用を持たない形で定義されている
    # ハイパーテキストを強連結成分（Strongly Connected Components）分解する
    # 有向グラフの強連結成分とは、その部分木であって任意の2頂点間に双方向に有向路がある（＝強連結である）ものを言う
    # Kosaraju のアルゴリズムに相当する
    def getSCCs(self, printsDetails: bool = False) -> set[frozenset[int]]:
        # ページをラベリングする
        hypertext = self.getHypertext()
        ## ラベリング関数の定義
        ## 削除されたページもラベリングされる
        def label(n: int = 0, pageIdToLabel: dict[int, int] = dict(), visitedPageIds: set[int] = set()) -> dict[int, int]:
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
                    for destinationId in hypertext.get(locationId):
                        n = label_oneway(destinationId, n) # 次のラベルの値を与え、再帰する
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
        pageIdToLabel = label()
        if printsDetails: print("Labelling:", pageIdToLabel)
        labelToPageId = {label: pageId for (pageId, label) in pageIdToLabel.items()}

        # ハイパーテキストの転置グラフ*を取得する
        transposeHypertext = Server.getTransposeHypertext(self.getHypertext())

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
                nonlocal pageIdToLabel
                nonlocal labelToPageId

                if printsDetails: print("labelling:", labelToPageId)
                if printsDetails: print("pageIdWithMaxLabel:", labelToPageId[max(labelToPageId.keys())])

                # ラベルが最大のページから強連結成分を取得する
                component = getOneComponent(labelToPageId[max(labelToPageId.keys())])

                # 分解された成分に割り当てられたラベリングの削除
                # 最大のラベルを取得しやすくする
                pageIdToLabel = {pageId: label for (pageId, label) in pageIdToLabel.items() if pageId not in component}
                labelToPageId = {label: pageId for (pageId, label) in pageIdToLabel.items()}
                if printsDetails: print("component:", component)

                # 分解された成分を強連結成分の集合に追加する
                foundComponents.add(component)

                # 再帰的にラベリングを続ける
                return getComponents(foundComponents, visitedPageIds)
            # すべてラベリングされているならば
            else:
                return foundComponents
            
        return getComponents()
    
    # 強連結成分分解（非再帰）
    def getSccs_nonrec(self, printsDetails: bool = False) -> set[frozenset[int]]:
         # ページをラベリングする
        """
        ラベリング手順（例）
        
        1 → 2 → 3
            ↘︎ ↑
            4 ⇄ 5
            
                                            ┌children visited?
        Stack   : numbered? : hasChild? : cnVsted?  : assigned number if qualified : note
        
        if      : False     : False     : None
                or : False     : True      : True      : then a number is assigned
                
        1       : False     : True      : False
        124     : False     : True      : False
        12425   : False     : True      : True      : 0
        1242    : False     : True      : False
        12423   : False     : False     : None      : 1
        1242    : False     : True      : True      : 2
        124     : False     : True      : True      : 3
        12      : True
        1       : False     : True      : True      : 4
        """
        
        hypertext = self.getHypertext()
        
        pageIdToLabel: dict[int, int] = dict()
        visitedPageIds: set[int] = set()
        n = 0
        
        # ラベリングされていないページがある限り
        while leftPageIds := hypertext.keys() - visitedPageIds:
            stack = [getMember(leftPageIds)]
            if printsDetails: print("Start labelling from", stack[0], "with", pageIdToLabel)
            
            # 適当なページから到達可能な全てのページに対してラベリングを行う
            while stack:
                locationId = stack.pop()
                if printsDetails: print(" Stack:", stack, "Now at", locationId)
                
                # すでにラベリングされているなら無視
                if locationId in pageIdToLabel:
                    if printsDetails: print("  Already labelled")
                    continue
                
                # 自身を周回済にする
                visitedPageIds.add(locationId)
                
                # ラベリングされるのは以下の場合
                # 未付番かつ以下のいずれかにあてはまる
                # 1. 消失している
                # 2. 子がいない
                # 3. 子が全て以下のいずれかにあてはまる
                #     1. 周回済（含付番済）である
                #     2. 親（自身）と同一である
                needLabelling = (destinationIds := hypertext.get(locationId)) is None \
                                or not destinationIds \
                                or destinationIds <= visitedPageIds | {locationId}
                if needLabelling:
                    if printsDetails: print("  Needs labelling")
                    pageIdToLabel[locationId] = n  # ラベリングする
                    n += 1                         # 次に付けられるべきラベルの値を返す
                # ラベリングするべきでない場合（リンク先を先に処理すべき場合）
                else:
                    if printsDetails: print("  Later; links:", hypertext.get(locationId))
                    visitedPageIds.add(locationId)
                    stack.append(locationId)
                    for destinaionId in hypertext.get(locationId):
                        stack.append(destinaionId)
        
        if printsDetails: print("Labelling:", pageIdToLabel)
        labelToPageId = {label: pageId for (pageId, label) in pageIdToLabel.items()}
        
        # ハイパーテキストの転置グラフを取得する
        transposeHypertext = Server.getTransposeHypertext(self.getHypertext())
                
        # 分解
        if printsDetails: print("——— Decomposing")
        components: set[frozenset[int]] = set()
        leftPageIds = set(pageIdToLabel.keys())
        
        while labelToPageId:
            if printsDetails: print("Components:", components)
            if printsDetails: print("Labelling :", labelToPageId)
            PageIdWithMaxLabel = labelToPageId[max(labelToPageId.keys())]
            stack = [PageIdWithMaxLabel]
            component = set()
            
            while stack:
                if printsDetails: print(" Stack     :", stack)
                
                locationId = stack.pop()
                
                # 強連結成分の一部として確定されるのは次のいずれかに当て嵌まったとき：
                # 1. （逆ハイパーテキスト上での）リンク先がない
                # 2. リンク先が全てすでに分離された強連結成分あるいは今分離しようとしている強連結成分に含まれる
                # 3. リンク先が全て強連結成分に含まれるか、周回済である
                needsExtracting = (destinationIds := transposeHypertext.get(locationId)) is None \
                                  or destinationIds <= component | (pageIdToLabel.keys() - labelToPageId.values()) \
                                  or destinationIds <= component | (pageIdToLabel.keys() - labelToPageId.values()) | set(stack)
                
                # 逆リンク先がない場合（もとのハイパーテキストでどこからもリンクされていない場合）
                if needsExtracting:
                    component.add(locationId)
                else:
                    if printsDetails: print("  Links found:", destinationIds)
                    component.add(locationId)
                    for destinationId in destinationIds:
                        # stack すべきは以下の全てを満たすもの
                        # 1. すでに別の成分の頂点として分離されていない（labelToPageId.values() に含まれる）
                        # 2. すでに component に含められていない
                        # 3. すでに stack に追加されていない
                        needsStacking = destinationId in labelToPageId.values() \
                                        and destinationId not in component \
                                        and destinationId not in stack
                        
                        if needsStacking:
                            stack.append(destinationId)
                            
                if printsDetails: print("  Component-update:", component)
            
            components.add(frozenset(component))
            labelToPageId = {label: pageId for (label, pageId) in labelToPageId.items() if pageId not in component}
        
        return components
    
    # 強結合成分の個数を取得する
    def hypertextIsStronglyConnected(self) -> int:
        return len(self.getSCCs())
    
    # ———その他
    # ハイパーリンクを辿って目的のページに辿り着くことを目指すゲーム
    def explore(self, treasure: int = None):
        # 与えられた str が int 形式に変換可能かを返す
        def isint(i: str) -> bool:
            try:
                int(i)
            except:
                return False
            else:
                return True

        # ハイパーリンクを辿る
        def proceed(locationId: int, walk: list[str] = []) -> int:
            # 現在地が目的地だった場合
            if locationId == treasure:
                print("→".join(walk)+("→" if walk else "")+str(locationId))
                print(f"You reached page {treasure}!")
                return 0
            # 現在地に相当するページが存在しなかった場合
            elif self.getPage(locationId) is None:
                print(f"Page {locationId} is gone!")
                proceed(int(walk[-1]), walk[:-1])
            # 現在地が目的地以外のページだった場合
            else:
                print("→".join(walk)+("→" if walk else "")+str(locationId)+"→"+str(self.getPage(locationId).destinationIds))
                v = input(f"Go to: ")
                
                # 入力値が"quit"だった場合
                if v == "quit":
                    return 1
                # 入力値が"back"だった場合
                elif v == "back":
                    if walk == []:
                        print("Can't go back. If you want to end the game, type \'quit\'.")
                        if proceed(locationId, walk): return 1
                    else:
                        if proceed(int(walk[-1]), walk[:-1]): return 1
                # 入力値が整数として解釈できなかった場合
                elif not isint(v):
                    print(f"Invalid input")
                    if proceed(locationId, walk): return 1
                # 入力値が整数として解釈される場合
                else:
                    destination = int(v)

                    # 入力されたページに現在地からアクセスできない場合
                    if destination not in self.getPage(locationId).destinationIds:
                        print(f"Can't move to {v}")
                        if proceed(locationId, walk): return 1
                    # 入力されたページに現在地からアクセスできる場合
                    else:
                        if proceed(destination, walk+[str(locationId)]): return 1

        # 目的地が与えられていない場合はランダムに決定する
        # 到達不能なページも候補にある
        # reconstruct するべきか？
        if treasure is None:
            treasure = random.choice(list(self.hypertext.keys() - {self.initialPageId}))
        
        print(f"Search for page {treasure}!")
        proceed(self.initialPageId)
    
    # リンクをランダムに選択して移動していくロボット
    def randomwalk(self, locationId: int = None, destinationId: int = None, maxStep: int = None, walk: list[str] = []):
        if locationId is None: locationId = self.initialPageId

        print(("→" if walk else "")+str(locationId), end="")
        # 現在地が目的地だった場合
        if locationId == destinationId:
            print(".")
            return
        # 歩数の上限に達した場合
        elif maxStep is not None and maxStep < 1:
            print("]")
            return
        # 現在地に相当するページが存在しなかった場合
        elif self.getPage(locationId) is None:
            print("/")
            return
        # 現在地が目的地以外のページだった場合
        else:
            choices = self.getPage(locationId).destinationIds
            self.randomwalk(random.choice(list(choices)), destinationId, (None if maxStep is None else maxStep-1), walk+[str(locationId)])




if __name__ == "__main__":
    """
        0   8 ← 10
      ↙︎ ⇅     ↘︎ ↑
  ⇨ 1 → 2       9 → 11
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ⇄ 12
      ↖︎ ↓ ↗︎ ↑
        7  (6)
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
    server.initialiseHypertext(0)
    print("hypertext:", server.getSortedHypertext())
    print("hyperlinks:", server.getSortedHyperlinks())
    # print(server.getRoot(), "is a root")
    # print(server.getSCCs())
    print(server.hypertextIsStronglyConnected(), "SCCs")
    print(server.hypertextIsStronglyConnected_nonrec(), "SCCs (nonrec)")
    # print("descendant of 7:", server.getdescendantPageIds(7))
    # print("descendant of 10:", server.getdescendantPageIds(10))
    print("\n——————————\n")
    
    """
       ~0~  8 ← 10
        ↑     ↘︎ ↑
    1 → 2       9 → 11
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ← 12
      ↖︎ ↓ ↗︎ ↑
        7 → 6
            ↑
           (13)
    """
    
    server.deletePage(0)
    page5.deleteLink(12)
    page7.addLink(6)
    page13 = Page(13, "n", {6})
    server.addPage(page13)
    server.crawlHypertext()
    print("hypertext:", server.getSortedHypertext())
    print("hyperlinks:", server.getSortedHyperlinks())
    # print(server.getRoot(), "is a root")
    # print(server.getSCCs(True))
    print(server.hypertextIsStronglyConnected(), "SCCs")
    print(server.hypertextIsStronglyConnected_nonrec(), "SCCs (nonrec)")
    # print("descendant of 7:", server.getdescendantPageIds(7))
    # print("descendant of 10:", server.getdescendantPageIds(10))
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
    """
    
    server.initialiseHypertext(13)
    print("hypertext:", server.getSortedHypertext())
    print("hyperlinks:", server.getSortedHyperlinks())
    # print(server.getRoot(), "is a root")
    # print(server.getSCCs())
    print(server.hypertextIsStronglyConnected(), "SCCs")
    print(server.hypertextIsStronglyConnected_nonrec(), "SCCs (nonrec)")
    # print("descendant of 7:", server.getdescendantPageIds(7))
    # print("descendant of 10:", server.getdescendantPageIds(10))
    print("\n——————————\n")
    
    # web.explore()
    
    # for _ in range(5):
    #     web.randomwalk(9, 3, 9)
    
    """
    ⇩
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
    servera.initialiseHypertext(20)
    print("hypertext:", servera.getSortedHypertext())
    print("hyperlinks:", servera.getSortedHyperlinks())
    # print(servera.getRoot(), "is a root")
    # print(servera.getSCCs())
    print(servera.hypertextIsStronglyConnected(), "SCCs")
    print(servera.hypertextIsStronglyConnected_nonrec(), "SCCs (nonrec)")
    # print("descendant of 20:", servera.getdescendantPageIds(20))
    # print("descendant of 22:", servera.getdescendantPageIds(22))
    print("\n——————————\n")

    """
    1 → 2 → 3
      ↘︎ ↑
        4 ⇄ 5
    """
    pageone = Page(1, "", {2, 4})
    pagetwo = Page(2, "", {3})
    pagethr = Page(3, "", set())
    pagefou = Page(4, "", {2, 5})
    pagefiv = Page(5, "", {4})
    serverserv = Server({pageone, pagetwo, pagethr, pagefou, pagefiv})
    serverserv.initialiseHypertext(1)
    print("hypertext:", serverserv.getSortedHypertext())
    print("hyperlinks:", serverserv.getSortedHyperlinks())
    print(serverserv.hypertextIsStronglyConnected(), "SCCs")
    print(serverserv.hypertextIsStronglyConnected_nonrec(), "SCCs (nonrec)")
    