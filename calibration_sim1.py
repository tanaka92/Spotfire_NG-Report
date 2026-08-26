# -*- coding: utf-8 -*-
# ================================================================
#  傾向管理線 適正化シミュレーション（σ係数 × m/nルール × NG率）
#
#  ■目的：傾向管理線の最適化。
#    (1) σ係数（管理線の幅 CL±k・σ_LOT）
#    (2) 判定ルール「n点中m点以上が管理線の外」
#    の2つを同時に振り、装置ch×項目×ルールごとに
#    「σ係数 → NG率」の検量線を CSV として出力する。
#    SpotfireでCSVを読み込み、装置ch・項目・ルールの3列でトレリスを組み、
#    x軸=σ係数 / y軸=NG率 の折れ線を引く前提。
#
#  ■方式B：Spotfireに再計算させない。
#    実測値・CL・σ_LOT を1項目につき1回だけ読み、
#    σ係数もm/nルールも Python の中で総当たり計算する。
#    → 表の走査は「項目数」回だけ。σ係数やルールを何通り増やしても
#      走査回数は増えない（旧版は σ係数の数だけ再計算していた）。
#
#  ■出力：calibration_data.csv（Shift_JIS、Excelでそのまま開ける）
#    列 = 項目, 装置ch, n, m, ルール, σ係数, OK, NG, 母数, NG率(%)
#
#  ■検証：BASE_K / BASE_N / BASE_M（＝現行の運用設定）で計算した結果を
#    実際の判定列と1行ずつ突き合わせ、一致率をログに出す。
#    ここが100%に近くなければ、CL・σ_LOT・ルールの解釈がDXP側とズレている。
#    まず items を数個に絞り、一致率を確認してから全項目に広げること。
# ================================================================

import clr
clr.AddReference('System.IO.Compression')
clr.AddReference('System.IO.Compression.FileSystem')
from System.IO import Directory,Path,File,StreamWriter
from System.Text import Encoding
from System import String,DateTime,Double
from System.Threading import Thread
from Spotfire.Dxp.Data import DataValueCursor

# ================================================================
#  設定（自分の環境に合わせて書き換える）★=要設定
# ================================================================
T="データ"                        # データテーブル名
JUDGE="＜判定列名＞"               # ★OK/NG/空 の判定列名（検証用。無ければ VERIFY=False に）
GRP="004_Gr_1"                    # 装置ch列名
PROP="項目1"                      # 項目切り替えプロパティ名
DATE_COL="＜加工日時列名＞"         # ★加工日時列（プロットの並び順を決める）
VAL_COL="＜実測値列名＞"            # ★実測値列
CL_COL="＜中心線列名＞"             # ★中心線CL列
SD_COL="σ_LOT"                    # σ_LOT列（ロット差の移動平均）
LOT_COL="＜ロットID列名＞"          # ★ロットID列（UNIT="lot" のときだけ使用）

SIGMA_VALUES=[1.0,1.5,2.0,2.5,3.0,3.5,4.0]      # 試すσ係数（検量線の横軸の点）
RULES=[(1,1),(3,2),(5,2),(5,3),(7,3),(7,4),(9,5)]  # 試す(n点中,m点以上)。(1,1)=単点判定
items=["工程A|膜厚|STEP","工程A|Rs|STEP"]         # テストは数項目。本番で全項目に

UNIT="wafer"                      # "wafer"=1行1プロット / "lot"=ロット平均を1プロット
ANCHOR="last"                     # NGの付け方 "last"=窓の最新点にNG / "any"=窓内の外れ点すべてにNG
MIN_TOTAL=30                      # 母数がこれ未満の装置chはCSVに出さない（不安定なので）
SLEEP_MS=400                      # 項目切り替え後の再計算待ち

VERIFY=True                       # 現行設定を判定列と突き合わせて検証するか
BASE_K=3.0; BASE_N=5; BASE_M=3    # ★現行の運用設定（σ係数・n点中・m点以上）

TEST_DIR=r"C:\Users\＜自分＞\Desktop\calib_test"

# ================================================================
#  出力フォルダ
# ================================================================
base=Path.Combine(TEST_DIR,"run_"+DateTime.Now.ToString("yyyyMMdd_HHmmss"))
Directory.CreateDirectory(base)

t=Document.Data.Tables[T]
gc=DataValueCursor.Create[String](t.Columns[GRP])
dc=DataValueCursor.Create[DateTime](t.Columns[DATE_COL])
vc=DataValueCursor.Create[Double](t.Columns[VAL_COL])
cc=DataValueCursor.Create[Double](t.Columns[CL_COL])
sc=DataValueCursor.Create[Double](t.Columns[SD_COL])
jc=DataValueCursor.Create[String](t.Columns[JUDGE]) if VERIFY else None
lc=DataValueCursor.Create[String](t.Columns[LOT_COL]) if UNIT=="lot" else None

def safe(s):
    for ch in u'\\/:*?"<>|': s=s.replace(ch,u"_")
    return s

# ================================================================
#  判定エンジン：外れ列 → n点中m点以上ルール → OK/NG
#    out[i] = 1 (|実測値-CL| > k*σ_LOT) / 0
#    ANCHOR="last": 窓[i-n+1..i]の合計>=m なら i をNG（窓が満たない先頭n-1点は判定しない）
#    ANCHOR="any" : 上の条件が成立した窓に含まれる「外れ点」をすべてNGにする
#  戻り値 = (OK数, NG数)
# ================================================================
def judge_idx(outs,n,m):
    """NGになった点の番号の集合と、判定対象の点数を返す"""
    N=len(outs); ng=set()
    if N<n: return (ng,0)                     # 窓が一度も満たない系列は判定しない
    run=0
    for i in range(N):
        run+=outs[i]
        if i>=n: run-=outs[i-n]               # 窓を1つ進める（先頭を落とす）
        if i>=n-1 and run>=m:
            if ANCHOR=="last": ng.add(i)      # 窓の最新点にNG
            else:
                for j in range(i-n+1,i+1):    # 窓内の外れ点すべてにNG
                    if outs[j]: ng.add(j)
    return (ng,N if ANCHOR=="any" else N-(n-1))

def judge_series(outs,n,m):
    ng,tot=judge_idx(outs,n,m)
    return (tot-len(ng),len(ng))

# ================================================================
#  データ収集 → シミュレーション
#    rows[(項目,装置ch,n,m,σ係数)] = (OK,NG)
# ================================================================
rows=[]; vok=0; vng=0; vtot=0
for it in items:
    Document.Properties[PROP]=it
    Thread.Sleep(SLEEP_MS)

    # --- 1項目につき1回だけ走査して、装置chごとの系列を作る ---
    cur=[gc,dc,vc,cc,sc]
    if VERIFY: cur.append(jc)
    if UNIT=="lot": cur.append(lc)
    seq={}
    for r in t.GetRows(*cur):
        g=gc.CurrentValue; dt=dc.CurrentValue
        if g is None or g=="" or dt is None: continue
        v=vc.CurrentValue; cl=cc.CurrentValue; sd=sc.CurrentValue
        if v is None or cl is None or sd is None: continue     # 判定不能点は系列に入れない
        j=jc.CurrentValue if VERIFY else None
        if UNIT=="lot":
            lo=lc.CurrentValue
            if lo is None or lo=="": continue
            bk=seq.setdefault(g,{}).setdefault(lo,[0.0,0.0,0.0,0,dt])
            bk[0]+=v; bk[1]+=cl; bk[2]+=sd; bk[3]+=1
            if dt>bk[4]: bk[4]=dt
        else:
            seq.setdefault(g,[]).append((dt,v,cl,sd,j))

    # --- ロット単位なら平均に畳む ---
    if UNIT=="lot":
        s2={}
        for g in seq:
            s2[g]=[(bk[4],bk[0]/bk[3],bk[1]/bk[3],bk[2]/bk[3],None) for bk in seq[g].values()]
        seq=s2

    # --- 装置chごとに σ係数 × ルール を総当たり ---
    for g in seq:
        pts=sorted(seq[g],key=lambda x:x[0])          # 加工日時順＝プロットの並び順
        if len(pts)<MIN_TOTAL: continue
        for k in SIGMA_VALUES:
            outs=[1 if abs(p[1]-p[2])>k*abs(p[3]) else 0 for p in pts]
            for (n,m) in RULES:
                ok,ng=judge_series(outs,n,m)
                tt=ok+ng
                if tt<MIN_TOTAL: continue
                rows.append((it,g,n,m,u"%d/%d"%(m,n),k,ok,ng,tt,100.0*ng/tt))

        # --- 検証：現行設定の結果を判定列と突き合わせる ---
        if VERIFY and UNIT=="wafer":
            outs=[1 if abs(p[1]-p[2])>BASE_K*abs(p[3]) else 0 for p in pts]
            calc,_tot=judge_idx(outs,BASE_N,BASE_M)
            for i in range(len(outs)):
                if i<BASE_N-1 and ANCHOR=="last": continue
                real=pts[i][4]
                if real not in ("OK","NG"): continue
                vtot+=1
                if (i in calc)==(real=="NG"): vok+=1
                else: vng+=1
    print "項目 %s : ch %d / 行 %d"%(it,len(seq),len(rows))

# ================================================================
#  CSV出力（Shift_JIS。Spotfireで読み込み、装置ch×項目×ルールでトレリス）
# ================================================================
sw=StreamWriter(Path.Combine(base,"calibration_data.csv"),False,Encoding.GetEncoding("shift_jis"))
sw.WriteLine(u"項目,装置ch,n,m,ルール,σ係数,OK,NG,母数,NG率(%)")
for it,g,n,m,rl,k,ok,ng,tt,rate in rows:
    sw.WriteLine(u"%s,%s,%d,%d,%s,%.2f,%d,%d,%d,%.4f"%(
        it.replace(u",",u"_"),g.replace(u",",u"_"),n,m,rl,k,ok,ng,tt,rate))
sw.Close()

print "=== 完了 ==="
print "CSV:",Path.Combine(base,"calibration_data.csv")
print "行数 %d （項目%d × ch × σ係数%d × ルール%d）"%(len(rows),len(items),len(SIGMA_VALUES),len(RULES))
print "単位=%s / NG付与=%s / 母数下限=%d"%(UNIT,ANCHOR,MIN_TOTAL)
if VERIFY and vtot:
    print "検証（現行 σ%.1f・%d点中%d点以上 vs 判定列）: 一致 %d / 不一致 %d / 対象 %d = 一致率 %.2f%%"%(
        BASE_K,BASE_N,BASE_M,vok,vng,vtot,100.0*vok/vtot)
    if 100.0*vok/vtot<95.0:
        print "  → 一致率が低い。CL/σ_LOT列の指定、ANCHOR（NGの付け方）、UNIT（wafer/lot）のどれかがDXP側と違う可能性。"
