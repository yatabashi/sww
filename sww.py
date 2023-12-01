"""
pageId は IP アドレスのようなもの → URL を与える
    content に似て非なるもの
    URL から IP を引く機構
点強連結度
ランダムなグラフの生成

トポロジカルソート ← 片方向連結（SCC縮約がそうなら元のグラフもそう）
    https://ja.wikipedia.org/wiki/%E3%83%88%E3%83%9D%E3%83%AD%E3%82%B8%E3%82%AB%E3%83%AB%E3%82%BD%E3%83%BC%E3%83%88#%E5%A4%96%E9%83%A8%E3%83%AA%E3%83%B3%E3%82%AF
    https://stackoverflow.com/questions/64326998/omn-algorithm-to-check-if-a-directed-graph-is-unilaterally-connected

ファイルシステム
    ハイパーテキスト：
    ・ページからなる
    ・どのページからどのページにも飛べる
    →閉路を含みうる
    
    ファイルシステム：
    ・ディレクトリとファイルからなる
    ・ディレクトリは親ディレクトリ、自分自身、子ディレクトリとファイルへのリンクを持つ
    　・複数のディレクトリに同じファイルが存在することもできる（ハードリンク）
    ・ファイルはリンクを持たない
    　・別のファイルを参照するファイルはありうる（シンボリックリンク／エイリアス）
    →原則として閉路は含まれない（ハードリンク等があれば可能）
"""


from typing import Type, Union
import copy
import random
import queue


# set から要素を一つ取り出す関数
def getMember(s: set) -> any:
    for m in s:
        return m


# set から要素をランダムに一つ取り出す関数
def getRandomMember(s: set) -> any:
    l = list(s)
    return random.choice(l)


# 集合のリストから、リスト内の全ての集合の和集合を得る関数
def mergeSets(l: list[set]) -> set:
    v = set()
    for s in l:
        v |= s
    return v


# リストに指定された要素が含まれればその index を、なければ -1 を返す
def find(l: list, i: any) -> int:
    if i in l:
        return l.index(i)
    else:
        return -1


# Webページに相当する
class Page:
    def __init__(self, id: int, destinationIds: set[int]):
        self.id: int = id
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
    def __init__(self, pages: set[Type[Page]] = None):
        if pages is None:
            pages = set()
        
        # ページIDとページを対応付ける
        self.record: dict[int, Type[Page]] = {page.id: page for page in pages}
    
    # ——— record に対する操作 ———
    
    # 指定の id を持つページを返す
    def getPage(self, id: int) -> Union[Page, None]:
        return self.record.get(id)
    
    # ページをサーバに追加する
    def addPage(self, *pages: Type[Page]):
        self.record.update({(page.id, page) for page in pages})
    
    # 指定したページをサーバから削除する（他のページからのリンクも削除する）
    def deletePage(self, *ids: int):
        # 出次数を0にする
        for id in ids:
            self.record.pop(id, None)
        
        # 入次数を0にする（他のページからのリンクを削除する）
        for id in ids:
            for page in self.record.values():
                page.deleteLink(id)
    
    # ——— ハイパーテキストの生成 ———
    
    def getHypertext(self):
        return {pageId: page.destinationIds for (pageId, page) in self.record.items()}
    
    # ハイパーテキストの構造をソートして返す
    def getSortedHypertext(self) -> dict[int, set[int]]:
        return dict(sorted(self.getHypertext().items(), key=(lambda x: x[0])))
    
    # 与えられたハイパーテキストの全てのリンクを反転させた転置グラフを生成する
    def getTransposeHypertext(self) -> dict[int, set[int]]:
        # 転置したリンクを取得する
        hyperlinks = self.getHyperlinks()
        pageIdsWithoutInEdge = {hyperlink[0] for hyperlink in hyperlinks} - {hyperlink[1] for hyperlink in hyperlinks}
        transposeHyperlinks = {hyperlink[::-1] for hyperlink in hyperlinks}
        
        # リンクからハイパーテキストを構築する
        transposeHypertext: dict[int, set[int]] = dict()
        
        for hyperlink in transposeHyperlinks:
            if hyperlink[0] in transposeHypertext:
                transposeHypertext[hyperlink[0]].add(hyperlink[1])
            else:
                transposeHypertext[hyperlink[0]] = {hyperlink[1]}
        
        transposeHypertext |= {pageId: set() for pageId in pageIdsWithoutInEdge}
        
        return transposeHypertext
    
    # ハイパーテキストを構築する
    def getInducedSubgraph(self, originId: int = None, constructed: dict[int, set[int]] = None) -> dict[int, set[int]]:
        def constructHypertextUniteratively(originId: int, constructed: dict[int, set[int]] = None) -> dict[int, set[int]]:
            if constructed is None:
                constructed = dict()
            
            # ページが周回済みだった場合
            if originId in constructed:
                return
            
            # ハイパーリンクを保存する
            location = self.getPage(originId)
            constructed[originId] = copy.copy(location.destinationIds)
            
            # リンク先の各ページを起点にハイパーテキストを構築する
            for i in location.destinationIds:
                descendantHypertext = constructHypertextUniteratively(i, constructed)
                if descendantHypertext is not None:
                    constructed |= descendantHypertext
            
            return constructed
    
        # 始点が指定されていない場合、全てのページから走査する
        if originId is None:
            leftPages = self.getPageIds()
            constructed = dict()
            while leftPages:
                constructed |= constructHypertextUniteratively(getMember(leftPages), constructed)
                leftPages -= constructed.keys()
        # 始点が指定されている場合、そのページから辿り着ける範囲のみ走査する
        else:
            constructed = constructHypertextUniteratively(originId)
            
        return constructed
    
    # ハイパーテキストを構築する（非再帰）
    def getInducedSubgraph_nonrec(self, originId: int = None):
        if originId is None:
            stack = [getMember(self.getPageIds())]
            leftPageIds = self.getPageIds()
        else:
            stack = [originId]
            leftPageIds = dict()
            
        hypertext: dict[int, set[int]] = dict()
        
        # 発見されたが未訪問のページが存在する限り
        while stack:
            locationId = stack.pop()
            
            # ページが未周回なら
            if locationId not in hypertext:
                destinationIds = self.getPage(locationId).destinationIds
                
                hypertext[locationId] = copy.copy(destinationIds)
                
                for destinationId in destinationIds:
                    if destinationId not in hypertext:
                        stack.append(destinationId)
            
            if originId is None:
                leftPageIds -= hypertext.keys()
                if leftPageIds and not stack:
                    stack = [getMember(leftPageIds)]
        
        return hypertext
    
    def SCCcontracted(self):
        sccs = self.getSCCs()
        rToIds = {min(scc): set(scc) for scc in sccs}
        idToR = {id: r for r, ids in rToIds.items() for id in ids}
        contraction = {key: set() for key in rToIds.keys()}
        
        for r, scc in rToIds.items():
            for pageId in scc:
                for destinationId in self.getPage(pageId).destinationIds:
                    if destinationId not in scc:
                        contraction[r] |= {idToR[destinationId]}
        
        return contraction
    
    # 推移簡約
    def transitiveReduction(self):
        """
        getdescendants と同様に巡回するが、二度目に訪れた時にそのページを記録し、元ページからそのページへのリンクを削除する

        各頂点の各リンクについて、そのリンクを通らずにリンク先に到達可能な場合、そのリンクを削除していく
        """
        tmpServer = copy.deepcopy(self)
        deletion = set()
        
        for startId in tmpServer.getPageIds():
            children = copy.copy(tmpServer.getPage(startId).destinationIds)
            
            if len(children) < 2:
                continue
            
            for endId in children:
                visited = {startId}
                stack = [child for child in children - {endId}]
                
                while stack:
                    locationId = stack.pop()
                    escapeFlag = False
                    
                    # ページが未周回なら
                    if locationId not in visited:
                        visited.add(locationId)
                        
                        for destinationId in tmpServer.getPage(locationId).destinationIds:
                            if destinationId == endId:
                                deletion.add((startId, endId))
                                tmpServer.getPage(startId).deleteLink(endId)
                                
                                escapeFlag = True
                                break
                            elif destinationId not in visited:
                                stack.append(destinationId)
                    
                    if escapeFlag:
                        break
        return deletion
    
    # ——— ハイパーテキストの情報取得 ———
    
    def getPageIds(self):
        return self.record.keys()
    
    # 与えられたハイパーテキストからハイパーリンクを得る
    def getHyperlinks(self) -> set[tuple[int, int]]:
        hypertext = self.getHypertext()
        
        s = set()
        
        # ハイパーリンクをタプルに変換する
        for (startId, endIds) in hypertext.items():
            s.update({(startId, endId) for endId in endIds})
        
        return s
    
    # ハイパーテキスト内の全リンクをソートして返す
    def getSortedHyperlinks(self) -> set[tuple[int, int]]:
        return sorted(list(self.getHyperlinks()))
    
    def getStartPageIds(self):
        return {pageId for (pageId, destinationIds) in self.getHypertext().items() if destinationIds}
    
    def getEndPageIds(self):
        return {pageId for (pageId, destinationIds) in self.getTransposeHypertext().items() if destinationIds}
    
    # 指定したページから到達可能なページのリストを取得する
    def getdescendantPageIds(self, originId: int) -> set[int]:
        descendants = set()
        stack = [originId]
        isFirst = True
        
        while stack:
            locationId = stack.pop()
            
            # ページが未周回なら
            if locationId not in descendants:
                if isFirst:
                    isFirst = False
                else:
                    descendants.add(locationId)
                
                destinationIds = self.getPage(locationId).destinationIds
                
                for destination in destinationIds:
                    if destination not in descendants:
                        stack.append(destination)
        
        return descendants
    
    # 始点と終点を指定し、その2ページ間の距離（到達に必要な最短のリンク数）を取得する
    def getDistance(self, startPageId: int, endPageId: int, printsDetails: bool = None):
        if printsDetails is None:
            printsDetails = False
        
        # 始点と終点の実在性を確認
        allPagesLinked = self.getPageIds()
        if not (startPageId in allPagesLinked and endPageId in allPagesLinked):
            return None
        
        # 始点と終点が同一の場合
        if startPageId == endPageId:
            return 0
        
        # 幅優先探索
        q = queue.Queue()
        q.put(startPageId)
        visited = {startPageId}
        depth = 0
        same = 1
        next = 0
        
        while q.queue:
            if same == 0:
                same = next
                next = 0
                depth += 1
            
            if printsDetails:
                print(depth, q.queue)
                print(" Left pages on the same level:", same)
                print(" pages on the next level     :", next)
            
            locationId = q.get()
            
            for destinationId in self.getHypertext().get(locationId):
                if destinationId == endPageId:
                    return depth + 1
                else:
                    if destinationId not in visited:
                        visited.add(destinationId)
                        next += 1
                        q.put(destinationId)
            
            same -= 1
        
        return None
    
    # ハイパーテキストを強連結成分（Strongly Connected Components）分解する
    # 強連結成分：その部分グラフであって、任意の2頂点間に双方向に有向路がある（＝強連結である）もの
    # Kosaraju のアルゴリズムに相当する
    def getSCCs(self, printsDetails: bool = None) -> set[frozenset[int]]:
        if printsDetails is None:
            printsDetails = False
        
        # ラベリング
        if printsDetails: print("——— Labelling")
        
        hypertext = self.getHypertext()
        
        # ラベリング関数の定義
        # 削除されたページもラベリングされる
        def label(n: int = None, pageIdToLabel: dict[int, int] = None,
                  visitedPageIds: set[int] = set()) -> dict[int, int]:
            if n is None:
                n = 0
            
            if pageIdToLabel is None:
                pageIdToLabel = dict()
            
            # 片道のラベリング関数の定義
            # 始点に戻ってきたら終了し、未周回のページを残しうる
            def label_oneway(locationId: int, n: int = None) -> int:
                if n is None:
                    n = 0
                
                # 周回済だった場合（処理済であるか、のちに処理されるので無視）
                if locationId in visitedPageIds:
                    if printsDetails: print(locationId, "has been visited")
                    
                    return n
                # リンク先がない場合
                elif not hypertext.get(locationId):
                    if printsDetails: print(locationId, "is a dead end. No.", n)
                    
                    visitedPageIds.add(locationId)  # 周回済にする
                    pageIdToLabel[locationId] = n   # ラベリングする
                    n += 1                          # 次のラベルの値をこのページのラベル + 1 にする
                    return n                        # 次に付けられるべきラベルの値を返す
                # リンク先がある場合
                else:
                    if printsDetails: print(locationId, "has links:")
                    
                    visitedPageIds.add(locationId)
                    # 各リンク先において片道のラベリングを行う
                    for destinationId in hypertext.get(locationId):
                        n = label_oneway(destinationId, n)  # 次のラベルの値を与え、再帰する
                    
                    if printsDetails: print(f"Came back to {locationId}. No.", n)
                    
                    pageIdToLabel[locationId] = n
                    n += 1
                    return n
            
            # ラベリングされていないページがあるならば
            if leftPageIds := hypertext.keys() - visitedPageIds:
                startPageId = getMember(leftPageIds)
                
                if printsDetails: print("Start labelling from", startPageId,
                                        "with", pageIdToLabel)
                
                # 適当なページから片道のラベリングを行う
                n = label_oneway(startPageId, n)
                
                # 再帰的にラベリングを続ける
                return label(n, pageIdToLabel, visitedPageIds)
            # すべてラベリングされているならば
            else:
                return pageIdToLabel
        
        # ラベリングの実行
        pageIdToLabel = label()
        labelToPageId = {label: pageId for (pageId, label) in pageIdToLabel.items()}
        
        if printsDetails: print("Labelling:", pageIdToLabel)
        
        # ハイパーテキストの転置グラフ*を取得する
        transposeHypertext = self.getTransposeHypertext()
        
        # 分解
        if printsDetails: print("——— Decomposing")
        
        # 分解関数の定義
        def getComponents(foundComponents: set[frozenset[int]] = None,
                          visitedPageIds: set[int] = set()) -> set[frozenset[int]]:
            if foundComponents is None:
                foundComponents = set()
            
            # 強連結成分を一つ取得する関数の定義
            # あるページから転置グラフを辿って到達可能な（自身をリンク先としている）ページの集合を返す
            def getOneComponent(locationId: int) -> frozenset[int]:
                # 周回済だった場合
                if locationId in visitedPageIds:
                    if printsDetails: print(" ", locationId, "is visited.")
                    
                    return frozenset()
                # リンク先がない場合
                elif not transposeHypertext.get(locationId):
                    if printsDetails: print(" ", locationId, "has no links.")
                    
                    visitedPageIds.add(locationId)  # 周回済にする
                    return frozenset({locationId})
                # リンク先がある場合
                else:
                    if printsDetails: print(" ", locationId, "has link:")
                    
                    visitedPageIds.add(locationId)
                    
                    rv = frozenset({locationId})
                    for destinaionId in transposeHypertext.get(locationId):
                        rv |= getOneComponent(destinaionId)
                        
                        if printsDetails: print(" Component is updated:", rv)
                    
                    return rv
            
            # 未周回のページがあるならば
            if transposeHypertext.keys() - visitedPageIds:
                nonlocal pageIdToLabel
                nonlocal labelToPageId
                
                if printsDetails: print("pageIdWithMaxLabel:", labelToPageId[max(labelToPageId.keys())])
                
                # ラベルが最大のページから強連結成分を取得する
                component = getOneComponent(labelToPageId[max(labelToPageId.keys())])
                
                # 分解された成分に割り当てられたラベリングの削除
                # 最大のラベルを取得しやすくする
                pageIdToLabel = {pageId: label
                                 for (pageId, label) in pageIdToLabel.items()
                                 if pageId not in component}
                labelToPageId = {label: pageId for (pageId, label) in pageIdToLabel.items()}
                
                if printsDetails: print("Component:", component)
                
                # 分解された成分を強連結成分の集合に追加する
                foundComponents.add(component)
                
                # 再帰的にラベリングを続ける
                return getComponents(foundComponents, visitedPageIds)
            # すべてラベリングされているならば
            else:
                if printsDetails: print("Components:", foundComponents)
                
                return foundComponents
        
        # ラベリングの実行
        return getComponents()
    
    # 強連結成分分解（非再帰）
    def getSccs_nonrec(self, printsDetails: bool = None) -> set[frozenset[int]]:
        if printsDetails is None:
            printsDetails = False
        
        # ページをラベリングする
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
                # 1. 子がいない
                # 2. 子が全て以下のいずれかにあてはまる
                #     1. 周回済（含付番済）である
                #     2. 親（自身）と同一である
                needLabelling = (not (destinationIds := hypertext.get(locationId))
                                 or destinationIds <= visitedPageIds | {locationId})
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
        transposeHypertext = self.getTransposeHypertext()
        
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
                # 1. リンク先が全て、以下のいずれかに該当する：
                #   1. 今分離しようとしている強連結成分に含まれる
                #   2. すでに分離された強連結成分に含まれる
                #   3. 周回済である
                needsExtracting = ((destinationIds := transposeHypertext.get(locationId))
                                   <= component
                                      | (pageIdToLabel.keys() - labelToPageId.values())
                                      | set(stack))
                
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
                        needsStacking = (destinationId in labelToPageId.values()
                                         and destinationId not in component
                                         and destinationId not in stack)
                        
                        if needsStacking:
                            stack.append(destinationId)
                
                if printsDetails: print("  Component-update:", component)
            
            components.add(frozenset(component))
            labelToPageId = {label: pageId
                             for (label, pageId) in labelToPageId.items()
                             if pageId not in component}
        
        return components
    
    # 強連結成分の個数を取得する
    def countSCCs(self) -> int:
        return len(self.getSCCs())
    
    # ハイパーテキストが強連結であるかどうかを返す
    def isStronglyConnected(self) -> bool:
        return self.countSCCs() == 1
    
    # ハイパーテキスト内のサイクル（closed path）を一つ返す
    def findCycle(self, pageIds: set[int] = None, printsDetails: bool = None) -> Union[list[int], None]:
        """
        0 → 1 → 2 → 3
        ↑       ↓   ↑
        7 ← 8 ← 4 → 6
        ↓   ↑
        9 → 5
        
        0 [] →
            1 [0] → 2
            2 [0, 1] → 3, 4
                3 [0, 1, 2] return [0, 1, 2]
                4 [0, 1, 2] → 6, 8
                    6 [0, 1, 2, 4] → 3
                        3 [0, 1, 2, 4, 6] /
                        /
                    8 [0, 1, 2, 4] → 7
                        7 [0, 1, 2, 4, 8] → 0, 9 ! '0124870'
        """
        if pageIds is None:
            pageIds = self.getPageIds()
        
        def f(locationId: int, path: int = None, deadEnds: set[int] = None, printsDetails: bool = None):
            if path is None:
                path = []
            
            if deadEnds is None:
                deadEnds = set()
            
            # ページが未訪問なら
            if (index := find(path, locationId)) == -1:
                if printsDetails: print(locationId, path)
                
                if destinationIds := self.getPage(locationId).destinationIds:
                    for destinationId in destinationIds:
                        if printsDetails: print(locationId, "to", destinationId, "of", destinationIds)
                        
                        if destinationId not in deadEnds and (rvs := f(destinationId, path+[locationId], deadEnds, printsDetails=printsDetails))[0] is not None:
                            if printsDetails: print("↩︎")
                            return rvs
                    
                    deadEnds.add(locationId)
                    
                    if printsDetails: print("No cycle found↩︎")
                    return (None, deadEnds)
                else:
                    deadEnds.add(locationId)
                    
                    if printsDetails: print("No Child↩︎")
                    return (None, deadEnds)
            else:
                if printsDetails: print("Cycle found↩︎")
                return (path[index:] + [locationId], deadEnds)
        
        # ある頂点から探索してサイクルが見つからなかったとき
        if (rvs := f(getMember(pageIds), printsDetails=printsDetails))[0] is None:
            # 経由した頂点を除いた残りの頂点があればサイクルを探索する
            if (left := pageIds - rvs[1]):
                return self.findCycle(left)
            # 全ての頂点を訪れていればサイクルは存在しない
            else:
                return None
        # サイクルが見つかったとき
        else:
            return rvs[0]
    
    # ハイパーテキスト内のサイクル（closed path）を一つ返す
    def findCycle_nonrec(self) -> Union[list[int], None]:
        # visited: set
        # path: list
        """
        0 → 1 → 2 → 3
        ↑       ↓   ↑
        7 ← 8 ← 4 → 6
        ↓   ↑
        9 → 5
        
        普通に深さ優先探索？
        1 → 2 → 4
            ↓ ↖︎ ↓
            3   5
        https://drken1215.hatenablog.com/entry/2023/05/20/200517#chap1
        stack; location; path; isvisited; haschild:ids
        ; 1; 1; false; true:2
        ; 2; 12; false; true:34
        4; 3; 12; false; false
        ; 4; 124; false; true:5
        ; 5; 1245; false; true:2 -> '2452'
        
        
        行き先がなければ pass
        行き先が記法なら return
        あれば append してすすむ
        """
        left = set(self.getPageIds())
        
        while left:
            stack = [getMember(left)]
            path = []
            
            while stack:
                locationId = stack.pop()
                
                # ページが未訪問なら
                if (index := find(path, locationId)) == -1:
                    left.discard(locationId)
                    
                    if destinationIds := self.getPage(locationId).destinationIds:
                        stack += list(destinationIds)
                        path.append(locationId)
                    else:
                        continue
                else:
                    return path[index:] + [locationId]
        
        return None
    
    def isDAG(self):
        return self.findCycle() is None
    
    def existsLinkTo404Page(self) -> bool:
        return bool(mergeSets((hypertext := self.getHypertext()).values()) - self.getPageIds())
    
    # ——— クラスメソッド ———
    
    # ハイパーテキストを元にページ群を（新たに）生成する
    @classmethod
    def makePagesFromHypertext(cls, hypertext: dict[int, set[int]]) -> set[Type[Page]]:
        return {Page(pageId, destinationIds) for pageId, destinationIds in hypertext.items()}
    
    # ハイパーリンクの集合を元にページ群を（新たに）生成する
    @classmethod
    def makePagesFromHyperlinks(cls, hyperlinks: set[tuple[int, int]]) -> set[Type[Page]]:
        d: dict[int, Page] = dict()
        
        for hyperlink in hyperlinks:
            if hyperlink[0] in d:
                d[hyperlink[0]].destinationIds.add(hyperlink[1])
            else:
                d[hyperlink[0]] = Page(hyperlink[0], {hyperlink[1]})
        
        
        if pageIdsWithoutOutEdge := {hyperlink[1] for hyperlink in hyperlinks} - {hyperlink[0] for hyperlink in hyperlinks}:
            d |= {pageId: Page(pageId, set()) for pageId in pageIdsWithoutOutEdge}
        
        return d.values()
    
    # 歩道の集合を辺の集合に変換する
    @classmethod
    def splitWalksIntoEdges(cls, walks: set[tuple[int, ...]]) -> set[tuple[int, int]]:
        edges: set[tuple[int, int]] = set()
        
        for walk in walks:
            previous = None
            
            for pageId in walk:
                if previous is not None:
                    edges.add((previous, pageId))
                    
                previous = pageId
        
        return edges
    
    # ——— その他 ———
    
    # リンクをランダムに選択して移動していくロボット
    def randomwalk(self, locationId: int = None,
                   destinationId: int = None, maxStep: int = None, walk: list[str] = None):
        if locationId is None:
            locationId = getRandomMember(self.record)
            
        if destinationId is None:
            destinationId = getRandomMember(self.getdescendantPageIds(locationId))
        
        if walk is None:
            walk = []
        
        print(("→" if walk else "")+str(locationId), end="")
        
        # 現在地が目的地だった場合
        if locationId == destinationId:
            print(".")
            return
        # 歩数の上限に達した場合
        elif maxStep is not None and maxStep < 1:
            print("]")
            return
        # それ以上進めない場合
        elif not (choices := self.getPage(locationId).destinationIds):
            print("/")
            return
        # 現在地が目的地以外のページだった場合
        else:
            self.randomwalk(random.choice(list(choices)),
                            destinationId, (None if maxStep is None else maxStep-1),
                            walk+[str(locationId)])
    
    # ハイパーリンクを辿って目的のページに辿り着くことを目指すゲーム
    def explore(self, treasure: int = None):
        # 与えられた str が int 形式に変換可能かを返す
        def isint(i: str) -> bool:
            try:
                int(i)
            except ValueError:
                return False
            else:
                return True
        
        # ハイパーリンクを辿る
        def proceed(locationId: int, walk: list[str] = None) -> int:
            if walk is None:
                walk = []
            
            # 現在地が目的地だった場合
            if locationId == treasure:
                print("→".join(walk)+("→" if walk else "")+str(locationId))
                print(f"You reached page {treasure}!")
                return 0
            # 現在地が目的地以外のページだった場合
            else:
                print("→".join(walk) + ("→" if walk else "")
                      + str(locationId) + "→" + str(self.getPage(locationId).destinationIds))
                
                v = input("Go to: ")
                
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
                    print("Invalid input")
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
        originId = getRandomMember(self.getStartPageIds())
        
        if treasure is None:
            treasure = random.choice(list(self.getdescendantPageIds(originId)))
        
        print(f"Search for page {treasure}!")
        proceed(originId)












if __name__ == "__main__":
    print("""
        0   8 ← 10
      ↙︎ ⇅     ↘︎ ↑
  ⇨ 1 → 2       9 → 11
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ⇄ 12
      ↖︎ ↓ ↗︎ ↑
        7   6
    
        0   8 ← 10
      ↙︎ ↑     ↘︎ ↑
  ⇨ 1   2       9 → 11
    ↓ ↗︎         ↑
    3 → 4 ← 5 ⇄ 12
      ↖︎ ↓ ↗︎ ↑
        7   6
    """)
    
    server = Server({Page(0, {1, 2}),
                     Page(1, {2, 3}),
                     Page(2, {0}),
                     Page(3, {2, 4}),
                     Page(4, {2, 7}),
                     Page(5, {4, 5, 12}),
                     Page(6, {5}),
                     Page(7, {3, 5}),
                     Page(8, {9}),
                     Page(9, {10, 11}),
                     Page(10, {8}),
                     Page(11, set()),
                     Page(12, {5, 9})})
    print("hypertext          :", server.getSortedHypertext())
    print("hyperlinks         :", server.getSortedHyperlinks())
    print("Descendants of 7   :", server.getdescendantPageIds(7))
    print("12 to 1            :", server.getDistance(12, 1), "links")
    print("12 to 10           :", server.getDistance(12, 10), "links")
    print("Start pages        :", server.getStartPageIds())
    print("End pages          :", server.getEndPageIds())
    print("Sccs               :", server.countSCCs())
    print("SCCs (nonrec)      :", len(server.getSccs_nonrec()))
    print("Cycle              :", server.findCycle())
    print("Cycle (nonrec)     :", server.findCycle_nonrec())
    print("is DAG             :", server.isDAG())
    print("SCC contraction    :", c := server.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server.existsLinkTo404Page())
    print("transitif reduction:", server.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
            8 ← 10
              ↘︎ ↑
    1 → 2       9 → 11
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ← 12
      ↖︎ ↓ ↗︎ ↑
        7 → 6
            ↑
            13
    
            8 ← 10
              ↘︎ ↑
    1   2       9 → 11
    ↓ ↗︎         ↑
    3 → 4 ← 5 ← 12
      ↖︎ ↓   ↑
        7 → 6
            ↑
            13
    """)
    
    server.deletePage(0)
    server.getPage(5).deleteLink(12)
    server.getPage(7).addLink(6)
    server.addPage(Page(13, {6}))
    print("hypertext          :", server.getSortedHypertext())
    print("hyperlinks         :", server.getSortedHyperlinks())
    print("Descendants of 7   :", server.getdescendantPageIds(7))
    print("12 to 1            :", server.getDistance(12, 1), "links")
    print("12 to 10           :", server.getDistance(12, 10), "links")
    print("Start pages        :", server.getStartPageIds())
    print("End pages          :", server.getEndPageIds())
    print("Sccs               :", server.countSCCs())
    print("SCCs (nonrec)      :", len(server.getSccs_nonrec()))
    print("Cycle              :", server.findCycle())
    print("Cycle (nonrec)     :", server.findCycle_nonrec())
    print("is DAG             :", server.isDAG())
    print("SCC contraction    :", c := server.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server.existsLinkTo404Page())
    print("transitif reduction:", server.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
   (1)→ 2       ...
    ↓ ↗︎ ↑   ∩   ↑
    3 → 4 ← 5 ←(12)
      ↖︎ ↓ ↗︎ ↑
        7 → 6
            ↑
            13⇦
    
        2
        ↑    
    3 → 4 ← 5
      ↖︎ ↓   ↑
        7 → 6
            ↑
            13⇦
    """)
    
    server_ = Server(Server.makePagesFromHypertext(server.getInducedSubgraph(13)))
    print("hypertext          :", server_.getSortedHypertext())
    print("hyperlinks         :", server_.getSortedHyperlinks())
    print("Descendants of 7   :", server_.getdescendantPageIds(7))
    print("5 to 13            :", server_.getDistance(5, 13), "links")
    print("13 to 5            :", server_.getDistance(13, 5), "links")
    print("Start pages        :", server_.getStartPageIds())
    print("End pages          :", server_.getEndPageIds())
    print("Sccs               :", server_.countSCCs())
    print("SCCs (nonrec)      :", len(server_.getSccs_nonrec()))
    print("Cycle              :", server_.findCycle())
    print("Cycle (nonrec)     :", server_.findCycle_nonrec())
    print("is DAG             :", server_.isDAG())
    print("SCC contraction    :", c := server_.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server_.existsLinkTo404Page())
    print("transitif reduction:", server_.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
    ⇩
    0 → 1 → 2 → 4
        ↑ ↙︎
        3
    """)
    
    server1 = Server({Page(20, {21}),
                      Page(21, {22}),
                      Page(22, {23, 24}),
                      Page(23, {21}),
                      Page(24, set())})
    print("hypertext          :", server1.getSortedHypertext())
    print("hyperlinks         :", server1.getSortedHyperlinks())
    print("Descendants of 21  :", server1.getdescendantPageIds(21))
    print("23 to 24           :", server1.getDistance(23, 24), "links")
    print("Start pages        :", server1.getStartPageIds())
    print("End pages          :", server1.getEndPageIds())
    print("Sccs               :", server1.countSCCs())
    print("SCCs (nonrec)      :", len(server1.getSccs_nonrec()))
    print("Cycle              :", server1.findCycle())
    print("Cycle (nonrec)     :", server1.findCycle_nonrec())
    print("is DAG             :", server1.isDAG())
    print("SCC contraction    :", c := server1.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server1.existsLinkTo404Page())
    print("transitif reduction:", server1.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
    ⇩
    1 → 2 → 3
      ↘︎ ↑
        4 ⇄ 5
          
    ⇩
    1   2 → 3
      ↘︎ ↑
        4 ⇄ 5
    """)
    
    server2 = Server({Page(1, {2, 4}),
                         Page(2, {3}),
                         Page(3, set()),
                         Page(4, {2, 5}),
                         Page(5, {4})})
    print("hypertext          :", server2.getSortedHypertext())
    print("hyperlinks         :", server2.getSortedHyperlinks())
    print("Descendants of 5   :", server2.getdescendantPageIds(5))
    print("5 to 3             :", server2.getDistance(5, 3), "links")
    print("Start pages        :", server2.getStartPageIds())
    print("End pages          :", server2.getEndPageIds())
    print("Sccs               :", server2.countSCCs())
    print("SCCs (nonrec)      :", len(server2.getSccs_nonrec()))
    print("Cycle              :", server2.findCycle())
    print("Cycle (nonrec)     :", server2.findCycle_nonrec())
    print("is DAG             :", server2.isDAG())
    print("SCC contraction    :", c := server2.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server2.existsLinkTo404Page())
    print("transitif reduction:", server2.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
    0 → 1 → 2 → 3
    ↑       ↓   ↑
    7 ← 8 ← 4 → 6
    ↓   ↑
    9 → 5
          
    0 → 1 → 2   3
    ↑       ↓   ↑
    7 ← 8 ← 4 → 6
    ↓   ↑
    9 → 5
    """)
    
    edges4 = Server.splitWalksIntoEdges({(0, 1, 2, 3), (2, 4, 6, 3), (4, 8, 7, 0), (7, 9, 5, 8)})
    server4 = Server(Server.makePagesFromHyperlinks(edges4))
    print("hypertext          :", server4.getSortedHypertext())
    print("hyperlinks         :", server4.getSortedHyperlinks())
    print("Descendants of 5   :", server4.getdescendantPageIds(5))
    print("5 to 1             :", server4.getDistance(5, 1), "links")
    print("Start pages        :", server4.getStartPageIds())
    print("End pages          :", server4.getEndPageIds())
    print("Sccs               :", server4.countSCCs())
    print("SCCs (nonrec)      :", len(server4.getSccs_nonrec()))
    print("Cycle              :", server4.findCycle())
    print("Cycle (nonrec)     :", server4.findCycle_nonrec())
    print("is DAG             :", server4.isDAG())
    print("SCC contraction    :", c := server4.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server4.existsLinkTo404Page())
    print("transitif reduction:", server4.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
    0 → 1 → 2 → 3
            ↓
            4
    """)
    
    edges5 = Server.splitWalksIntoEdges({(0, 1, 2, 3), (2, 4)})
    server5 = Server(Server.makePagesFromHyperlinks(edges5))
    print("hypertext          :", server5.getSortedHypertext())
    print("hyperlinks         :", server5.getSortedHyperlinks())
    print("Descendants of 3   :", server5.getdescendantPageIds(3))
    print("3 to 1             :", server5.getDistance(3, 1), "links")
    print("Start pages        :", server5.getStartPageIds())
    print("End pages          :", server5.getEndPageIds())
    print("Sccs               :", server5.countSCCs())
    print("SCCs (nonrec)      :", len(server5.getSccs_nonrec()))
    print("Cycle              :", server5.findCycle())
    print("Cycle (nonrec)     :", server5.findCycle_nonrec())
    print("is DAG             :", server5.isDAG())
    print("SCC contraction    :", c := server5.SCCcontracted())
    print("contraction is DAG :", Server(Server.makePagesFromHypertext(c)).isDAG())
    print("soundness          :", not server5.existsLinkTo404Page())
    print("transitif reduction:", server5.transitiveReduction())
    
    print("\n———————————\n")
    
    print("""
    0 → 1
    ↓
   ~2~
    """)
    
    server6 = Server({Page(0, {1, 2}),
                      Page(1, set())})
    print("hypertext          :", server6.getSortedHypertext())
    print("soundness          :", not server6.existsLinkTo404Page())
    print("transitif reduction:", server6.transitiveReduction())
    
    print("\n———————————\n")
    
    # for _ in range(10):
    #     server.randomwalk(12, 3, 14)
    
    # print("\n———————————\n")
    
    # server.explore()
