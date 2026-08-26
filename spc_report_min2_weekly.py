# -*- coding: utf-8 -*-
# ================================================================================
# 【週次化改修 変更箇所一覧】原本 spc_report_min2.py(673行) → 実コード726行
# 「★変更N」「★追加N」で検索すると該当箇所に飛べる。「#★旧|」の行が改修前の原文。
#  1  ヘッダの期間説明を新仕様(NG率8日/ルール30日/画像全期間)に差替
#  2  変数辞書に新規変数10件(ia,ib,ic,ie,ii,ig,ih,ij,ik,im)を追記
#  3  n=7→n=8(NG率窓)、ia=30(ルール判定窓)を新設
#  4  ルール名7種の末尾に「｜過去30日」を明記
#  5  診断用リスト ii=[] を追加／ib(30日TimeSpan)を新設
#  6  ic=項目内の最新加工日時／ie=停止ch集合(C案)の算出
#  7  NG率窓の適用条件に「かつ停止chでない」を追加
#  8  集計区分ラベル判定に停止chを反映([全期間]表示)
#  9  ルール判定窓30日フィルタ(ロット単位の系列収集)
# 10  ルール判定窓30日フィルタ(ウエハ単位の系列収集)
# 11  診断:30日窓内の点数を記録
# 12  差分スキップ比較を先頭4フィールドに限定(状態5フィールド化に伴う回帰修正)
# 13  ルール継続回数の算出と状態5番目への保存(ik/ij/ig/ih/im)
# 14  一覧表の掲載条件を「NG>0 または ルール検出あり」に
# 15  gs():推移特徴に「新規/継続N回目」を併記＋到達不能だったσ分岐を除去
# 16  hc():行の背景色を指定できるよう引数を追加
# 17  本文タイトルを「トピックス」に変更／期間の注意書きを新仕様に差替
# 18  一覧表の検出行に背景色を適用
# 19  ルール別トピックスに「新規/継続N回目」を併記＋σ分岐を除去
# 20  詳細HTMLのh1を「NG率レポート（自動配信）」に変更／期間注意書き差替／CSSの%%→%(既知バグ修正)
# 21  詳細HTMLの書式引数に ia を追加
# 22  完了ログの期間表示を新仕様に差替
# 23  診断print(窓内点数の分布・ゲート未達件数・各ルールの点数到達率)
# 24  メール件名を「NG率レポート（トピックス付き・自動配信）」に変更
# ================================================================================
# 【二重計上対策 改修（annotated1 → 本版）】「▲修正N」で検索。「#▲旧|」が改修前の原文。
#  ■背景：データ抽出がロット単位のため、工程Cのロットを先週分で引くと、その同じロットが
#    　　　通過した工程A/Bの「先々週以前」の行まで一緒にテーブルへ入ってくる。
#    　　　旧実装のNG率窓は「そのchの最新加工日時から8日」という“ch相対”の窓だったので、
#    　　　最新が先々週のchでは窓が先々週側にスライドし、＝先週すでに配信した行をもう一度数える。
#    　　　結果、悪化幅トップ(差分)からは「差分ゼロ」で落ちるのに、NG率トップ(絶対値)には
#    　　　先週と全く同じ内容が毎週上がり続ける。
#  ■方針：期間を“時計”で切るのをやめ、「前回配信以降に新しく入った加工日時の行だけを数える」
#    　　　＝キー単位の水位線(watermark)方式に変更する。既報行は何度テーブルに現れても数えない。
#  1  実行基準時刻 jd を導入（DateTime.Now を全体で1回だけ取得）
#  2  状態文字列に6番目「前回集計済みの最終加工日時(ticks)」を追加（ja=読取 / jc=前回水位線）
#  3  NG率集計を「ch最新から8日」→「前回配信以降の新規行のみ」へ（初登場chは全期間）
#  4  停止ch判定(ic/ie)を廃止。新規行が無いchは“0”ではなく“非掲載”にする
#  5  判定値の表記ゆれ(前後空白/全角)を吸収＋OK/NG以外の値の件数を診断出力
#  6  ルール判定窓を「ch最新から30日」→「実行時刻から30日」（本文の仕様どおり自然に消える）
#  7  状態は上書きではなくマージ保存（新規行が無いkeyの水位線・継続回数・前回値を失わない）
#  8  画像の描画対象を jo に一本化／トレリス頁名→ch の解決を正規化マッチ化
#  9  画像ラベル・本文・詳細HTML・完了ログの期間表記を新仕様に差替
# 10  診断print（既報スキップ件数／未知判定値／掲載ch数 ほか）
# 11  グラフ1枚ごとに「全期間の同じ集計」を参考値として毎回併記（判定には不使用）
# 12  TEST実行では既定で状態を保存しない（ao の意味を反転）
# 13  状態の保存形式をV2に圧縮（項目名の番号化＋日時のbase36化。約半分）
# 14  判定値の読み取りを期間フィルタより前に出し、全期間の集計を同じ1パスで取る
# 15  状態の確定を配信成功後に移動。送信失敗時は保存せず成果物も残す
# 16  実行のたびにコード版数を記録し、変わっていれば差分を出力（コード履歴）
# 17  前回状態の保存先を状態ファイル ks 一本に統一（文書プロパティへの保存を廃止）。
#     読めなかった回は不問とし、全keyを初回（全期間集計）として続行する
# 18  コード履歴からコード全体の複製を廃止。台帳に「変更前／変更後の行」だけを追記する
#     （code_changes.tsv）。履歴フォルダのファイルは4つ固定で増え続けない
# ================================================================================
# SPC NG率レポート 自動配信（最短化版）。動作は spc_report_integrated.py と同一。
#===== ★変更1 ここから ===== ヘッダの期間説明を新仕様(NG率8日/ルール30日/画像全期間)に差替
#★旧| # 集計期間：既存装置ch=最新加工日時から直近PERIOD_DAYS日／初回=全期間。管理線は全体計算前提。
#★旧| # 期間（週次実行前提）：NG率等=chの最新加工日時から直近n日(=8)／初登場ch・停止ch(最新が窓より古い)=全期間。
#★旧| # 　　　　　　　　　　ルール判定=chの最新加工日時から直近ia日(=30)、全ルール一律・ゲートu点(=8)。画像=全期間表示。
# 期間（週次実行前提）：NG率等=前回配信以降に追加された加工日時の行のみ／初登場ch=全期間。   #▲修正9
# 　　　　　　　　　　ルール判定=実行時刻から直近ia日(=30)、全ルール一律・ゲートu点(=8)。画像=全期間表示。   #▲修正9
#===== ★変更1 ここまで =====
# ============ 変数辞書（自動生成・改名は挙動不変）★=会社で実値に要設定 ============
# 記法: 短縮名 = 意味  [元の名前]。'汎用'はスコープ違いで同名を使い回している一時変数。
# a   = DP=Document.Properties 文書プロパティ索引子
# b   = DD=Document.Data データ管理(Tables/Properties)
# c   = DVC=DataValueCursor.Create カーソル生成
# d   = CMB=Path.Combine パス連結
# e   = SLP=Thread.Sleep 待機(ms)
# f   = 表名「データ」
# g   = 判定列名 ★
# h   = 装置ch(グループ)列名
# i   = 項目切替プロパティ名
# j   = 対象グラフ名 ★
# k   = σ係数プロパティ名(SIGMA_K)
# l   = 移動平均Nプロパティ名(MA_N)
# m   = 加工日時列名 ★
# n   = 集計期間(日) PERIOD_DAYS ※本版では「水位線が無い既存key」の移行用フォールバック窓
# o   = 実測値列名 ★
# p   = 中心線列名 ★
# q   = σ列名(σ_LOT)
# r   = ロットID列名 ★
# s   = 既定集計単位('lot')
# t   = 単位例外の項目リスト
# u   = ルール判定の最小点数
# v   = ルール種類別トップ件数
# w   = 画像幅px
# x   = 画像高px
# y   = JPEG品質
# z   = 送信元メール
# aa  = 送信先メール
# ab  = SMTPサーバ ★
# ac  = SMTPポート
# ad  = 項目一覧プロパティ名(項目A)
# ae  = 項目一覧のソース列(任意)
# af  = 悪化トップ件数
# ag  = NG率トップ件数
# ah  = 新規トップ件数
# ai  = 表掲載の最小NG率
# aj  = TESTモード
# ak  = NGページのみ出力
# al  = 差分のみ出力
# am  = メール送信可否
# an  = TEST:前回状態を固定
# ao  = TEST:状態を保存しない
# ap  = テスト出力先フォルダ
# aq  = 前回状態プロパティ名 ←▲修正17で廃止（状態は ks のファイルにのみ保存）
# ar  = 出力ルート(TEST_DIR/Temp)
# at  = 実行フォルダ(run_日時)
# au  = 画像フォルダ
# av  = 対象データテーブル
# aw  = 関数 gi():項目一覧を取得
# ax  = 前回NG率(gi内は候補プロパティ) [pr]
# ay  = 汎用:属性名/キー生成の第1引数 [a]
# az  = 汎用:候補値/ビジュアル [v]
# ba  = 汎用ループ要素 [x]
# bb  = 例外オブジェクト [e]
# bc  = gi経路B:列ノード [nd]
# bd  = 汎用:ノード/NG合計 [n]
# be  = 監視項目一覧 [items]
# bf  = 対象トレリスグラフ [vc]
# bg  = ページ(ビジュアル探索) [pg]
# bh  = 判定列カーソル [jc]
# bi  = 装置ch列カーソル [gc]
# bj  = 加工日時カーソル [dc]
# bk  = 実測値カーソル [vcur]
# bl  = 中心線カーソル [clcur]
# bm  = σカーソル [sdcur]
# bn  = ロットIDカーソル [lotcur]
# bo  = 関数 ec():HTMLエスケープ
# bp  = 文字列引数(エスケープ/整形) [s]
# bq  = 関数 sf():ファイル名サニタイズ
# br  = 禁止文字ループ [ch]
# bs  = 関数 ps():状態文字列→(OK,NG,係数,MA)
# bt  = パース対象文字列 [val]
# bu  = 汎用:点辞書/分割片 [p]
# bv  = 関数 cr():NG率%計算
# bw  = OK数 [ok_c]
# bx  = NG数 [ng_c]
# by  = 母数=OK+NG [tt]
# bz  = 関数 mk():キー生成 項目\x1f装置ch
# ca  = 汎用:キー第2引数/画像Bitmap [b]
# cb  = 関数 sp():キー分解
# cc  = 汎用キー [k]
# cd  = K0:ソートキー(先頭要素)
# ce  = NA:「該当なし」HTML
# cf  = ルール名:突発異常(外れ)
# cg  = ルール名:トレンド
# ch  = ルール名:片側シフト
# ci  = ルール名:変動拡大(不安定化)
# cj  = ルール名:貼り付き
# ck  = ルール名:変動縮小(前兆)
# cl  = ルール名:振動
# cm  = 関数 zn():規格化Z値
# co  = メール本体MailMessage [m]
# cp  = 関数 dr():推移ルール検出
# cq  = 点列 [pts]
# cr  = 突発判定フラグ [isp]
# cs  = トレンド系判定フラグ [iot]
# ct  = ルール検出結果辞書 [out]
# cu  = Z値リスト [z]
# cv  = 値の列(実測値) [vv]
# cw  = 最大|Z|(突発) [mx]
# cx  = Zループ変数 [zi]
# cy  = 連続カウンタ [run]
# cz  = 最大連続(トレンド) [mr]
# da  = 前回変化方向 [dr2]
# db  = ループindex [i]
# dc  = 汎用:方向差分/日時値 [d]
# dd  = 正方向連長 [ru]
# de  = 負方向連長 [rd]
# df  = 片側最大連長 [msd]
# dg  = |Z|<1最大連長(貼り付き) [mi]
# dh  = 交互カウンタ [cnt]
# di  = 汎用:前回符号/集計期間TimeSpan [pd]
# dj  = 交互最大連長(振動) [mo]
# dk  = 前後半の境目 / HTML本文h [h]
# dl  = 前半のσ_LOT平均（変動判定）
# dm  = 後半のσ_LOT平均（変動判定）
# dn  = RULE_UNIT:ルール→単位
# do  = RULE_ORDER:ルール表示順
# dp  = JPEGエンコーダ
# dq  = 汎用ループ変数:エンコーダ/セル [c]
# dr  = JPEG品質パラメータ [_ep]
# ds  = 前回状態辞書 [prev]
# dt  = 前回状態の生文字列 [raw]
# du  = 状態行ループ [ln]
# dv  = 今回状態辞書 [cur]
# dw  = rows:(項目,NG,母数,率)
# dx  = 詳細HTMLセクション群 [pa]
# dy  = 失敗(例外)リスト [fl]
# dz  = 生成画像数 [nimg]
# ea  = 差分スキップ数 [nskip]
# eb  = 画像記録(率,項目,ch,OK,NG,path,fn) [ur]
# ec  = 集計区分 key→「前回以降/初回(全期間)/移行」 [us]
# ed  = ルール検出結果 key→{種類:程度} [rh]
# ee  = 現在の監視項目 [it]
# ef  = 今回σ係数 [k_now]
# eg  = 今回移動平均N [n_now]
# eh  = 装置ch→「判定のある行」の最新加工日時（診断用）
# eh0 = 装置ch→全行の最新加工日時（トレリス頁の母集合用）   #▲修正3
# ei  = 行イテレータ(値未使用) [r]
# ej  = 汎用:装置ch値/レコード [u]
# ek  = 項目内NG数 [ng]
# el  = 項目内母数 [tot]
# em  = 装置ch→NG数 [ung]
# en  = 装置ch→OK数 [uok]
# eo  = 合成キー 項目\x1f装置ch [key]
# ep  = 汎用の一時日時 [lu]
# eq  = 今回集計できた装置ch集合 [allu]
# er  = 装置ch [u2]
# es  = ロット単位集計フラグ [is_lot]
# et  = 集計用カーソル一覧 [rc]
# eu  = 装置ch→系列(日時,値,CL,σ) [se]
# ev  = 装置ch→wafer生系列 [ws]
# ew  = ロット集約バッファ [acc]
# ex  = 中心線値 [cl]
# ey  = σ値 [sd]
# ez  = ロットID [lot]
# fa  = ロット集約レコード/ロット群 [a/lots]
# fb  = 系列リスト/UL入力 [lst]
# fc  = 検出結果詳細(種類→程度) [det]
# fd  = wafer生系列ソート済 [wl]
# fe  = wafer点列 [wp]
# ff  = 装置ch順リスト [gp]
# fg  = 装置ch値(順序取得) [gg]
# fh  = 詳細HTML断片群 [ig]
# fi  = トレリス [tr]
# fj  = ページ数 [pc]
# fk  = ページindex [pi]
# fl  = 対象装置ch(ページ) [gn]
# fm  = 表示ラベル用ch名 [lg]
# fn  = 描画Graphics [g]
# fo  = 画像ファイル名 [fn]
# fp  = OK数(ページ) [oc]
# fq  = NG数(ページ) [nc]
# fr  = NG率 [rt]
# fs  = 画像ラベルHTML [lab]
# ft  = key→画像(path,fn) [ibk]
# fu  = 項目名(トピック) [it2]
# fv  = 装置ch名(トピック) [grp]
# fw  = 画像パス [imf]
# fx  = 全ch集計(率,項目,ch,OK,NG,key) [cu]
# fy  = 今回状態パース結果 [cp]
# fz  = 全体母数 [g_tot]
# ga  = 全体NG合計 [g_ng]
# gb  = 全体NG率 [g_rate]
# gc  = NGのある今回ch数 [ng_now]
# gd  = 前回OK合計 [p_ok]
# ge  = 前回NG合計 [p_ng]
# gf  = 前回NGありch数 [ng_prev]
# gg  = 前回状態パース結果 [pp]
# gh  = 前回全体NG率 [g_rate_prev]
# gi  = 悪化リスト(Δ,項目,ch,…) [wk]
# gj  = NG率差分Δ [dl]
# gk  = NG率トップ [top]
# gl  = NGある全ch(率順) [nt]
# gm  = 新規発生リスト [nu]
# gn  = 改善リスト [ip]
# go  = 今回NG率(改善計算) [nr]
# gp  = ルール種類別トップ辞書 [rtp]
# gq  = ルール種類 [kind]
# gr  = 程度 [sev]
# gs  = 関数 fo():推移特徴の整形文字列
# gt  = 特徴文字列の一時配列 [o]
# gu  = ルール単位記号 [un]
# gv  = 種類別リスト [lst]
# gw  = 関数 bth():メール本文HTML生成
# gx  = 画像srcを返す関数(引数) [img_src]
# gy  = 関数 IMG():画像タグ or 画像なし
# gz  = 画像タグ用サフィックス [tag]
# ha  = 画像情報(path,fn) [im]
# hb  = 関数 TD():表セル
# hc  = 関数 ROW():表行
# hd  = セル値の並び [cs]
# he  = 関数 UL():箇条書き
# hf  = 各項目の整形関数 [fmt]
# hg  = 関数 SEC():見出し+一覧+画像
# hh  = 見出し文字列 [title]
# hi  = 画像タグ接頭辞 [tp]
# hj  = 表の順位カウンタ [rk]
# hk  = 推移特徴文字列 [ft]
# hl  = 表示用特徴(空は―) [fd]
# hm  = 画像通番カウンタ [ci/ri]
# hn  = 詳細HTMLの表本体 [srows]
# ho  = 詳細HTMLのCSS [css]
# hp  = 詳細HTML全体 [html]
# hq  = 書き込みStreamWriter [sw]
# hr  = 関数 プレビュー用src(相対パス)
# hs  = cid/サフィックス引数 [cid]
# ht  = zipファイルパス [zippath]
# hu  = メール埋込画像リスト [linked]
# hv  = 関数 メール用src(cid)
# hw  = 埋込画像リソース [lr]
# hx  = メール本文(プレビュー/送信) [body]
# hy  = HTMLビュー(AlternateView) [av]
# hz  = 添付zip [at]
# jw  = 画像未取得chの記録
# jp  = トレリス表示頁の退避
# jq  = 項目選択の退避
# jt  = 除外ch集合(OK皆無かつNGあり)
# jf  = 突発:系列の代表スケール(中央値|v|)
# jg  = 突発:|値-CL|
# jh  = 突発:程度の分母(CL or 系列規模)
#===== ★追加2 ここから ===== 変数辞書に新規変数10件(ia,ib,ic,ie,ii,ig,ih,ij,ik,im)を追記
# --- 週次化(2026-07)で追加 ---   #★追加2
# ia  = ルール判定窓(日)=30   #★追加2
# ib  = ルール判定窓のTimeSpan   #★追加2
#★旧| # ic  = 項目内の最新加工日時（停止ch判定の基準点）   ←▲修正4で廃止
#★旧| # ie  = 停止ch集合（最新がNG率窓より古い→全期間集計）  ←▲修正4で廃止
# ii  = 診断:ルール判定系列の窓内点数リスト   #★追加2
# ig  = 前回のルール継続回数 key→{ruleidx:回数}   #★追加2
# ih  = 今回のルール継続回数 key→{ruleidx:回数}   #★追加2
# ij  = 関数 状態5番目フィールド→継続回数辞書   #★追加2
# ik  = ルール名→インデックス（表示順doに基づく）   #★追加2
# im  = 関数 表示用「新規／継続N回目」   #★追加2
#===== ★追加2 ここまで =====
# --- 二重計上対策(本版)で追加 ---   #▲修正1
# jd  = 実行基準時刻（DateTime.Now を1回だけ取得して全体で共有）   #▲修正1
# jb  = 既報除外(水位線)の有効フラグ。Falseで旧来の“実行時刻からn日”窓に退避   #▲修正3
# ja  = 関数 状態6番目フィールド→前回集計済みの最終加工日時(DateTime|None)   #▲修正2
# jc  = key→前回集計済みの最終加工日時（＝水位線。これ以前の行は二度と数えない）   #▲修正2
# jm  = key→今回“数えた”行の最新加工日時（次回の水位線として保存）   #▲修正2
# jl  = key→今回の新規判定行数（0なら非掲載）   #▲修正3
# jn  = 保存用のマージ後状態辞書   #▲修正7
# jo  = 画像描画の対象ch集合（今回集計あり ∪ ルール検出あり）   #▲修正8
# jz  = 正規化ch名→実ch名（トレリス頁名の解決用）   #▲修正8
# jr  = 診断カウンタ辞書(skip=既報スキップ/old=移行窓スキップ/unk=未知判定値)   #▲修正10
# jy  = 関数 保存用の状態文字列を7フィールドで組み立てる   #▲修正7
# jk  = 汎用:このkeyの水位線   #▲修正3
# jx  = 前回の配信で実際に掲載されたkey集合（前回サマリの母集合）   #▲修正7
# ji/je/jj = 診断:既報スキップ/移行窓スキップ/未知判定値（項目内カウンタ）   #▲修正10
# 状態フィールド: OK;NG;係数;MA;継続回数;水位線ticks;更新した実行時刻ticks   #▲修正2/7
# ================================================================================
import clr
clr.AddReference('System.Drawing'); clr.AddReference('System.IO.Compression'); clr.AddReference('System.IO.Compression.FileSystem')
from System.Drawing import Bitmap,Rectangle,Graphics,Color
from System.Drawing.Imaging import ImageFormat,Encoder,EncoderParameter,EncoderParameters,ImageCodecInfo
from System.IO import Directory,Path,File,StreamWriter
from System.IO.Compression import ZipFile
from System.Text import Encoding
#★旧| from System import String,DateTime,TimeSpan,Double
from System import String,DateTime,TimeSpan,Double,Int64   # Int64=水位線(ticks)の復元用   #▲修正2
from System.Threading import Thread
from Spotfire.Dxp.Application.Visuals import VisualContent
from Spotfire.Dxp.Data import DataValueCursor,DataPropertyClass

# エイリアス（頻出のロング呼び出しを短縮。挙動は不変）
a=Document.Properties          # 文書プロパティ（読み書きの索引子）
b=Document.Data                # データマネージャ（Tables / Properties）
c=DataValueCursor.Create      # 値カーソル生成（総称メソッド群 DVC[型](列)）
d=Path.Combine                # パス連結
e=Thread.Sleep                # 待機(ms)

# ┌─【区分】設定 ──────────────────────────────────────────────────────────
# │ 対象   f=表名  g=判定列  h=装置ch列  m=加工日時列  o=実測値  p=中心線  q=σ_LOT  r=ロットID
# │ 画面   i=項目切替プロパティ  j=対象グラフ名  k=σ係数プロパティ  l=移動平均Nプロパティ  ad=項目一覧プロパティ  ae=項目一覧の列
# │ 期間   n=移行用の窓(日)  ia=ルール判定窓(日)  jd=実行基準時刻  jb=水位線方式のON/OFF
# │ 判定   s=既定の集計単位  t=単位が逆の項目  u=ルール判定の最小点数  v=種類別トップ件数
# │ 掲載   af=悪化  ag=NG率  ah=新規 の各トップ件数  ai=表掲載の最小NG率
# │ 画像   w,x=画像の幅高  y=JPEG品質
# │ 配信   z=送信元  aa=送信先  ab=SMTPサーバ  ac=SMTPポート
# │ モード aj=TEST  ak=NGページのみ  al=差分のみ  am=送信可否  an=TEST:前回状態を固定  ao=TEST:状態を保存する
# │ 保存   ap=TEST出力先  ks=状態ファイル(必須)  kt=失効日数  kh/kj/kc=コード履歴の設定  ※文書プロパティ保存は廃止
# └──────────────────────────────────────────────────────────────────────────
f="データ"; g="＜判定列名＞"; h="004_Gr_1"; i="項目1"; j="＜グラフ名＞"
k="SIGMA_K"; l="MA_N"
#===== ★変更3 ここから ===== n=7→n=8(NG率窓)、ia=30(ルール判定窓)を新設
#★旧| m="＜加工日時列名＞"; n=7
m="＜加工日時列名＞"; n=8; ia=30   # n=移行用フォールバック窓(日) / ia=ルール判定窓(日)   #★変更3 #▲修正3
#===== ★変更3 ここまで =====
o="＜実測値列名＞"; p="＜中心線列名＞"; q="σ_LOT"; r="＜ロットID列名＞"
s="lot"; t=[]   # 例外に挙げた項目だけ既定と逆の単位
u=8; v=10
w,x=1200,480; y=22
z="yourname@corp.jp"; aa="spc-group@corp.jp"; ab="＜SMTPサーバー＞"; ac=25
ad="項目A"; ae=None
af=10; ag=10; ah=10
ai=0.0
aj=True; ak=True; al=False; am=True
an=False; ao=False
#★旧| ap=r"C:\Users\＜自分＞\Desktop\spc_test"; aq="SPC_PrevState"
ap=r"C:\Users\＜自分＞\Desktop\spc_test"   # aq(文書プロパティ名)は▲修正17で廃止。状態は ks のファイルにのみ保存する   #▲修正17
#★旧| ao=False   # 旧仕様:「TEST時に状態を保存しない」フラグ（既定Falseなので保存されていた）
#  ▲修正12: 意味を反転。既定(False)ではTEST実行時に状態を保存しない。   #▲修正12
#           TESTで水位線を進めて本番配信分を食う事故を既定で防ぐ。連続テストで保存したいときだけTrue。
#===== ▲修正1 ここから ===== 実行基準時刻を1回だけ取得（以降の期間判定は全てこれを基準にする）
jd=DateTime.Now   # 実行基準時刻。ch相対ではなくこの時刻を基準にすることで期間が毎回同じ意味になる   #▲修正1
jb=True           # True=既報行を水位線で除外（推奨） / False=旧来型の“実行時刻からn日”窓に退避   #▲修正3
#===== ▲修正1 ここまで =====
#===== ▲修正13 ここから ===== 状態の保存先（文書プロパティの容量制限を回避）
# ks に書き込み可能なパスを入れると、前回状態をそのテキストファイルに保存する（文書プロパティは使わない）。
# ★必須設定★ 文書プロパティへの保存は廃止したので、ここが空だと前回状態を持ち越せず、
# 毎回すべてのkeyが初回（全期間集計）になる。Spotfire Serverへの負荷はゼロ、容量制限も無い。
# 複数ノードでジョブが動く場合は、必ずUNC共有など全ノードから見える場所を指定すること。   #▲修正17
ks=u""            # 例: ur"\\＜サーバ＞\＜共有＞\spc\spc_state.txt"   #▲修正13
kt=180            # 状態の失効日数。この日数更新の無いkeyは保存時に捨てる（0で無効）   #▲修正13
#===== ▲修正13 ここまで =====
#===== ▲追加16 ここから ===== コード履歴（実行のたびに版数を記録し、変わっていれば差分を出力）
kh=u""            # 履歴の保存先フォルダ。空なら 出力ルート\code_history   #▲追加16
kj=u""            # Spotfireに登録したスクリプト名（ScriptManager経由で本文を取る場合に指定）   #▲追加16
kc=u""            # マスター.pyのパス。上記で本文が取れない環境ではここから読む（最終手段）   #▲追加16
#===== ▲追加16 ここまで =====

# ┌─【区分】出力フォルダとデータテーブル ──────────────────────────────────
# │ ar=出力ルート(TEST_DIR または Temp)   at=実行フォルダ run_日時   au=画像フォルダ   av=対象データテーブル
# └──────────────────────────────────────────────────────────────────────────
ar=ap if aj else Path.GetTempPath()
if not Directory.Exists(ar): Directory.CreateDirectory(ar)
#★旧| at=d(ar,"run_"+DateTime.Now.ToString("yyyyMMdd_HHmmss"))
at=d(ar,"run_"+jd.ToString("yyyyMMdd_HHmmss"))   #▲修正1
au=d(at,"img"); Directory.CreateDirectory(au)

#===== ▲追加16 ここから ===== コード履歴：版数の記録と差分出力
# ┌─【区分】コード履歴 ────────────────────────────────────────
# │ kg()=本文のSHA1先頭12桁（＝版数）      kk()=スクリプト本文の取得（戻り: 本文, 取得経路）
# │ km()=版数の判定・差分作成・履歴追記    kz=メール等に出す版数表示   ky=今回の差分テキスト
# │ kT()=TSVセル用の整形   kE()=変更前/変更後の対応表を作る   kM=明細の1実行あたり上限
# │ 出力先(kh または 出力ルート\code_history)。ファイルは4つだけで、増え続けない:
# │   code_history.tsv  … 1実行1行の要約台帳（変更があった回だけ追記）
# │   code_changes.tsv  … 1変更1行の明細台帳（種別・旧行・新行・変更前・変更後）★履歴の本体
# │   latest.py         … 次回の比較に使う土台。毎回上書き（版ごとの複製は残さない）
# │   latest_diff.txt   … 直近の差分(unified)。毎回上書き
# │   変更があった回は 実行フォルダにも code_diff.txt を置くので添付zipで配布される
# └──────────────────────────────────────────────────────
try:   # 差分生成。difflibが無い環境でも履歴が止まらないよう簡易版を用意する
    import difflib
    def kD(ay,bt,c1,c2): return u"\n".join(difflib.unified_diff(ay.splitlines(),bt.splitlines(),fromfile=c1,tofile=c2,lineterm=u""))
except ImportError:
    def kD(ay,bt,c1,c2):
        a1=ay.splitlines(); b1=bt.splitlines(); s1=set(a1); s2=set(b1)
        bp=[u"--- %s"%c1,u"+++ %s"%c2,u"(difflibが使えないため、行の増減だけの粗い差分です)"]
        for db,du in enumerate(b1,1):
            if du not in s1: bp.append(u"+%d: %s"%(db,du))
        for db,du in enumerate(a1,1):
            if du not in s2: bp.append(u"-%d: %s"%(db,du))
        return u"\n".join(bp)
from System.Security.Cryptography import SHA1
#===== ▲修正18 ここから ===== コード全体の複製をやめ、台帳に「変更前／変更後の行」だけを残す
kM=2000   # 1実行あたりの明細行の上限（大規模な入れ替えで台帳が膨らむのを防ぐ）   #▲修正18
def kT(bp):   # TSVのセルに入れられる形へ整形（タブ・改行を落とし、極端に長い行は切る）
    bp=bp.replace(u"\t",u"    ").replace(u"\r",u"").replace(u"\n",u" ")
    return bp if len(bp)<=1000 else bp[:1000]+u"…（以下略）"
def kE(ay,bt):   # 前版と今版から (種別,旧行,新行,変更前,変更後) の一覧を作る
    a1=ay.splitlines(); b1=bt.splitlines(); ct=[]
    try:
        for tg,i1,i2,j1,j2 in difflib.SequenceMatcher(None,a1,b1).get_opcodes():
            if tg=="equal": continue
            if tg=="replace":       # 置き換え＝変更前と変更後を1行に並べる
                for db in range(max(i2-i1,j2-j1)):
                    ct.append((u"変更",
                        unicode(i1+db+1) if i1+db<i2 else u"",
                        unicode(j1+db+1) if j1+db<j2 else u"",
                        kT(a1[i1+db]) if i1+db<i2 else u"",
                        kT(b1[j1+db]) if j1+db<j2 else u""))
            elif tg=="delete":
                for db in range(i1,i2): ct.append((u"削除",unicode(db+1),u"",kT(a1[db]),u""))
            elif tg=="insert":
                for db in range(j1,j2): ct.append((u"追加",u"",unicode(db+1),u"",kT(b1[db])))
    except:      # difflibが無い環境: 行の増減だけを記録する（前後の対応づけはしない）
        s1=set(a1); s2=set(b1); ct=[]
        for db,du in enumerate(b1,1):
            if du not in s1: ct.append((u"追加",u"",unicode(db),u"",kT(du)))
        for db,du in enumerate(a1,1):
            if du not in s2: ct.append((u"削除",unicode(db),u"",kT(du),u""))
    if len(ct)>kM: ct=ct[:kM]+[(u"以降省略",u"",u"",u"",u"変更が%d行を超えたため省略。全文は latest_diff.txt を参照"%kM)]
    return ct
#===== ▲修正18 ここまで =====
def kg(bp):   # 版数＝本文のSHA1先頭12桁
    try:
        ba=SHA1.Create().ComputeHash(Encoding.UTF8.GetBytes(bp))
        return u"".join(u"%02x"%(bd&0xff) for bd in ba)[:12]
    except: return u"?"
def kk():     # 本文の取得。環境によって取れる経路が違うので順に試す
    try:
        if u"__file__" in globals() and __file__ and File.Exists(__file__):
            return File.ReadAllText(__file__,Encoding.UTF8),u"__file__"
    except: pass
    try:      # Spotfireに登録したスクリプトから取得（APIの形は版により違うため2通り試す）
        if kj:
            ba=Document.ScriptManager.TryGetScript(kj)
            if ba and ba[0] and ba[1] is not None: return ba[1].ScriptCode,u"ScriptManager(%s)"%kj
    except: pass
    try:
        for ba in Document.ScriptManager.GetScripts():
            if (not kj) or ba.Name==kj: return ba.ScriptCode,u"ScriptManager:%s"%ba.Name
    except: pass
    try:
        if kc and File.Exists(kc): return File.ReadAllText(kc,Encoding.UTF8),u"マスターファイル"
    except: pass
    return None,u"取得不可"
def km():
    bt,bp=kk()
    if bt is None:
        print "WARN スクリプト本文を取得できません（kj にスクリプト名、または kc にマスター.pyのパスを設定してください）"
        return u"版数不明",None
    cc=kg(bt); ba=kh or d(ar,u"code_history")
    try:
        if not Directory.Exists(ba): Directory.CreateDirectory(ba)
    except Exception,bb:
        print "WARN コード履歴フォルダを作成できません:",bb; return u"版数 %s"%cc,None
    bd=d(ba,u"latest.py"); ay=None
    try:
        if File.Exists(bd): ay=File.ReadAllText(bd,Encoding.UTF8)
    except: ay=None
    if ay is not None and kg(ay)==cc:
        print "コード履歴: 変更なし（版数 %s / 取得元 %s）"%(cc,bp)
        return u"版数 %s（前回から変更なし）"%cc,None
    ct=None   #▲修正18: 版ごとのファイル名を作らなくなったので日時文字列(az)は不要になった
    if ay is not None: ct=kD(ay,bt,u"前回 %s"%kg(ay),u"今回 %s"%cc)
    cu=len([1 for du in (ct or u"").split(u"\n") if du[:1]==u"+" and du[:3]!=u"+++"])
    cw2=len([1 for du in (ct or u"").split(u"\n") if du[:1]==u"-" and du[:3]!=u"---"])
#===== ▲修正18 ここから ===== 版ごとの.py複製と日時つきdiffをやめ、台帳2本＋上書き2本に集約
#★旧|         File.WriteAllText(d(ba,u"code_%s_%s.py"%(az,cc)),bt,Encoding.UTF8)   # 版ごとの複製
#★旧|         if ct: File.WriteAllText(d(ba,u"diff_%s.txt"%az),ct,Encoding.UTF8)   # 日時つきの差分
    try:
        File.WriteAllText(bd,bt,Encoding.UTF8)                                    # 次回の比較の土台（毎回上書き）
        if ct: File.WriteAllText(d(ba,u"latest_diff.txt"),ct,Encoding.UTF8)       # 直近の差分（毎回上書き）
        if not File.Exists(d(ba,u"code_history.tsv")):
            File.WriteAllText(d(ba,u"code_history.tsv"),u"日時\t版数\t前版数\t取得元\t行数\t追加\t削除\n",Encoding.UTF8)
        File.AppendAllText(d(ba,u"code_history.tsv"),u"%s\t%s\t%s\t%s\t%d\t%d\t%d\n"%(
            jd.ToString("yyyy-MM-dd HH:mm:ss"),cc,kg(ay) if ay is not None else u"-",bp,len(bt.splitlines()),cu,cw2),Encoding.UTF8)
        if ay is not None:                                                        # 明細台帳＝変更前/変更後だけを追記
            cy2=kE(ay,bt)
            if cy2:
                if not File.Exists(d(ba,u"code_changes.tsv")):
                    File.WriteAllText(d(ba,u"code_changes.tsv"),u"日時\t版数\t前版数\t種別\t旧行\t新行\t変更前\t変更後\n",Encoding.UTF8)
                az2=jd.ToString("yyyy-MM-dd HH:mm:ss"); ay2=kg(ay)
                File.AppendAllText(d(ba,u"code_changes.tsv"),u"".join(
                    u"%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%((az2,cc,ay2)+ba2) for ba2 in cy2),Encoding.UTF8)
                print "コード履歴: 変更行 %d 件を code_changes.tsv に記録"%len(cy2)
    except Exception,bb:
        print "WARN コード履歴の書き込みに失敗:",bb
#===== ▲修正18 ここまで =====
    if ct:
        try: File.WriteAllText(d(at,u"code_diff.txt"),ct,Encoding.UTF8)   # 添付zipにも同梱
        except: pass
        print "コード履歴: 変更あり 版数 %s（+%d/-%d行・取得元 %s）"%(cc,cu,cw2,bp)
        return u"版数 %s（前回から +%d／−%d 行）"%(cc,cu,cw2),ct
    print "コード履歴: 初回記録 版数 %s（取得元 %s）"%(cc,bp)
    return u"版数 %s（履歴の初回記録）"%cc,None
kz,ky=km()
#===== ▲追加16 ここまで =====

av=b.Tables[f]

# 項目一覧：候補値メンバー→列ノードの順で試し、ダメなら手動代入
# BUG?: 経路A/BはSpotfire更新でAPI変化→全滅しうる。その時は下の手動リストに落ちる。
# ┌─【区分】項目一覧の取得 ────────────────────────────────────────────────
# │ aw()=項目一覧を返す関数   be=監視項目の一覧   ax/ay/az/ba/bb/bc/bd=関数内の一時変数
# │ 経路A=文書プロパティの候補値 → 経路B=列ノード → 手動リスト の順に試す
# └──────────────────────────────────────────────────────────────────────────
def aw():
    try:
        ax=b.Properties.GetProperty(DataPropertyClass.Document,ad)
        for ay in ("Values","ValidValues","PossibleValues","Categories","AllowedValues"):
            if hasattr(ax,ay):
                try:
                    az=[ba for ba in list(getattr(ax,ay)) if ba not in (None,"")]
                    if az: print "items:経路A .%s %d件"%(ay,len(az)); return az
                except: pass
    except Exception,bb: print "経路A失敗:",bb
    try:
        if ae:
            bc=Document.ActiveDataTableReference.Columns[ae].Hierarchy.Levels.LeafLevel.TryGetNodes(2147483647)
            az=[bd.FormattedValue for bd in bc[1] if bd.FormattedValue not in (None,"") and str(bd.FormattedValue)!="None"]
            if az: print "items:経路B %s %d件"%(ae,len(az)); return az
    except Exception,bb: print "経路B失敗:",bb
    print "経路A・B不可→手動代入"; return None
be=aw()
if not be:
    be=[u"工程A|膜厚|STEP",u"工程A|Rs|STEP",u"工程B|CD|STEP"]   # ←実項目名に置換（キー生成がunicode前提のためu""必須）   #▲修正8
    print "items手動:",len(be)

# ┌─【区分】ビジュアル参照と列カーソル ────────────────────────────────────
# │ bf=対象トレリスグラフ   bh=判定列  bi=装置ch列  bj=加工日時  bk=実測値  bl=中心線  bm=σ_LOT  bn=ロットID
# │ カーソルはここで1回だけ作り、以降のGetRowsで使い回す
# └──────────────────────────────────────────────────────────────────────────
bf=[az.As[VisualContent]() for bg in Document.Pages for az in bg.Visuals if az.Title==j][0]
bh=c[String](av.Columns[g]); bi=c[String](av.Columns[h])
bj=c[DateTime](av.Columns[m])
bk=c[Double](av.Columns[o]); bl=c[Double](av.Columns[p])
bm=c[Double](av.Columns[q]); bn=c[String](av.Columns[r])

# ┌─【区分】小道具（文字列とキーの操作） ──────────────────────────────────
# │ bo()=HTMLエスケープ  bq()=ファイル名の禁止文字を置換  jv()=表記ゆれ吸収キー(空白/記号/大小文字を無視)
# │ bs()=状態文字列→(OK,NG,係数,MA)  bv()=NG率%の計算(母数0は0.0)
# │ bz()=キー生成 項目\x1f装置ch   cb()=キー分解   cd()=先頭要素でソート   ce=「該当なし」のHTML
# └──────────────────────────────────────────────────────────────────────────
def bo(bp): return bp.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def bq(bp):
    for br in u'\\/:*?"<>|': bp=bp.replace(br,u"_")
    return bp
def bs(bt):
    try: bu=bt.split(u";"); return (int(bu[0]),int(bu[1]),bu[2],bu[3])
    except: return None   # 形不正→None（比較スキップ）
def bv(bw,bx):
    by=bw+bx; return (100.0*bx/by) if by else 0.0   # BUG?: tt=0でゼロ割回避
bz=lambda ay,ca:u"%s\x1f%s"%(ay,ca); cb=lambda cc:cc.split(u"\x1f",1); cd=lambda ba:ba[0]; ce=u'<p>該当なし</p>'   # キー生成/分解・ソートキー・該当なし
#===== ▲修正8 ここから ===== 表記ゆれ吸収キーの定義を前倒し（トレリス頁名の解決でも使うため）
def jv(cc): return cc.replace(u" ",u"").replace(u"\u3000",u"").replace(u"-",u"").replace(u"_",u"").lower()   # 表記ゆれ吸収キー   #▲修正8
#===== ▲修正8 ここまで =====

import math

#===== ▲修正13 ここから ===== 状態のコーデック（V2形式）と入出力
# 【なぜ形式を変えるか】旧形式は1keyあたり「項目名(長い)+OK;NG;係数;MA;継続;ticks(19桁);ticks(19桁)」で
#   100文字前後になり、文書プロパティの容量を圧迫していた。V2は
#     ・項目名を番号化してヘッダに1回だけ書く
#     ・日時を2000-01-01起点の秒のbase36（6文字）にする
#   ことで1keyあたり40文字前後に縮む（約6割減）。内部表現は従来のまま（";"区切り7フィールド）なので
#   集計・比較のコードには一切手を入れていない。読み込みは旧形式(V1)も受け付ける。
# ┌─【区分】状態のコーデック（保存形式V2） ──────────────────────────────
# │ ke=base36の基点(2000-01-01)  k3=base36の文字表  k6()=DateTime→base36秒  k7()=その逆
# │ kd()=区切り文字のサニタイズ  kr()=テキスト→内部辞書(+壊れた行数)  kw()=内部辞書→V2テキスト(+失効)
# │ kl()=状態ファイルの読み込み(読めなければNone＝全key初回扱い)   kp()=状態ファイルへの書き込み(一時ファイル経由)
# └──────────────────────────────────────────────────────────────────────────
ke=DateTime(2000,1,1); k3=u"0123456789abcdefghijklmnopqrstuvwxyz"
def k6(dc):   # DateTime→base36秒。水位線が実時刻より前に戻らないよう切り上げる（＝既報を数え直さない）
    bd=int(math.ceil(dc.Subtract(ke).TotalSeconds))
    if bd<0: bd=0
    bp=u""
    while bd>0: bp=k3[bd%36]+bp; bd=bd//36
    return bp or u"0"
def k7(bp):   # base36秒→DateTime
    bd=0
    for br in bp: bd=bd*36+k3.index(br)
    return ke.AddSeconds(bd)
def kd(bp):   # 区切り文字の混入で状態が壊れるのを防ぐ（B5対策）
    return bp.replace(u"\t",u" ").replace(u"\r",u"").replace(u"\n",u" ").replace(u"=",u"＝").replace(u";",u"；")
def kr(bt):   # テキスト→内部辞書{key:"OK;NG;係数;MA;継続;水位線;更新"} + 壊れた行数
    ct={}; ci={}; bd=0
    if not bt: return ct,0
    for du in bt.split(u"\n"):
        du=du.strip(); du=du.strip(u"\r")
        if not du: continue
        if du[:2]==u"#V": continue
        if du[:2]==u"#I":
            bu=du.split(u"\t")
            if len(bu)>=2: ci[bu[0][2:]]=bu[1]
            else: bd+=1
            continue
        if u"\t" in du:                      # V2行: idx,ch,OK,NG,係数,MA,継続,水位線,更新
            bu=du.split(u"\t")
            if len(bu)<9 or bu[0] not in ci: bd+=1; continue
            ct[bz(ci[bu[0]],bu[1])]=u";".join(bu[2:9])
        elif u"=" in du:                     # V1行(旧形式・移行用)
            cc,bp=du.rsplit(u"=",1)
            if len(bp.split(u";"))<2 or not cc: bd+=1; continue
            ct[cc]=bp
        else: bd+=1
    return ct,bd
def kw(ct):   # 内部辞書→V2テキスト（失効を適用）。戻り値=(テキスト,採用件数,失効件数)
    ci={}; co2=[]; bd=0
    for cc in sorted(ct):
        try: fu,fv=cb(cc)
        except: continue
        ep2=ja(ct[cc],6)
        if kt and ep2 is not None and ep2<jd.AddDays(-kt): bd+=1; continue   # 失効
        bu=ct[cc].split(u";")
        while len(bu)<7: bu.append(u"")
        fu=kd(fu); fv=kd(fv)
        if fu not in ci: ci[fu]=unicode(len(ci))
        co2.append(u"\t".join([ci[fu],fv]+[kd(ba) for ba in bu[:7]]))
    bp=[u"#V2"]+[u"#I%s\t%s"%(ci[fu],fu) for fu in sorted(ci,key=lambda ba:int(ci[ba]))]+co2
    return u"\n".join(bp),len(co2),bd
#★旧| def kl(): ... ファイル→文書プロパティ の順で読む／def kp(bt): ... 失敗時は文書プロパティへ退避
#  ▲修正17: 文書プロパティへの保存を廃止し、状態ファイル ks 一本に統一。   #▲修正17
#    読み書きの先が食い違って水位線が巻き戻る経路（古いファイル＋新しいプロパティ）を根から断つ。
#    読めなかった場合は「前回状態なし」＝全keyを初回扱い（全期間集計）として続行する。
def kl():     # 状態の読み込み: 状態ファイルのみ。読めなければ None（＝全key初回扱い）   #▲修正17
    if not ks:
        print "WARN 状態ファイル ks が未設定です。前回状態を使わず、全keyを初回（全期間集計）として処理します"
        return None
    try:
        if not File.Exists(ks):
            print "状態: ファイルが未作成です（初回実行 or 保存先の変更）→ 全keyを初回として処理します: %s"%ks
            return None
        bt=File.ReadAllText(ks,Encoding.UTF8)
        print "状態: ファイルから読込 %s"%ks
        return bt
    except Exception,bb:
        print "WARN 状態ファイルの読込に失敗→全keyを初回として処理します:",bb
        return None
def kp(bt):   # 状態の書き込み: 状態ファイルのみ。一時ファイル経由で置換するので途中終了でも壊れない   #▲修正17
    if not ks:
        print "ERROR 状態ファイル ks が未設定のため保存できません（次回も全keyが初回扱いになります）"
        return u"保存先なし"
    try:
        bp=Path.GetDirectoryName(ks)
        if bp and not Directory.Exists(bp): Directory.CreateDirectory(bp)
        File.WriteAllText(ks+u".tmp",bt,Encoding.UTF8)
        if File.Exists(ks): File.Delete(ks)
        File.Move(ks+u".tmp",ks)
        return u"ファイル(%s)"%ks
    except Exception,bb:
        print "ERROR 状態ファイルの書込に失敗:",bb
        print "ERROR 今回の水位線は記録されていません。次回は全keyが初回（全期間集計）になります: %s"%ks
        return u"保存失敗"
#===== ▲修正13 ここまで =====

# ┌─【区分】推移パターンの判定 ────────────────────────────────────────────
# │ cf=突発異常 cg=トレンド ch=片側シフト ci=変動拡大 cj=貼り付き ck=変動縮小 cl=振動（ルール名の文字列）
# │ dn=ルール→程度の単位   do=ルールの表示順   me()=中央値   cm()=規格化Z値(σ≒0はNone)
# │ cp(点列,突発判定するか,トレンド系を判定するか)=検出結果{ルール名:程度}
# │ 点列の各要素は {"v":実測値,"cl":中心線,"sd":σ_LOT} の辞書
# └──────────────────────────────────────────────────────────────────────────
#===== ★変更4 ここから ===== ルール名7種の末尾に「｜過去30日」を明記
#★旧| cf,cg,ch,ci,cj,ck,cl=u"大きく外れた点がある（突発異常｜CL±6σ_LOTを超過）",u"値が一方向に動き続けている（トレンド｜同方向に6点以上連続）",u"中心から片側にずれ続けている（CLの同じ側に9点以上連続）",u"変動が大きくなってきている（不安定化｜後半のσ_LOTが前半の1.8倍超）",u"値がほとんど動いていない（貼り付き｜CL±1σ_LOT内に15点以上連続）",u"変動が小さくなってきている（貼り付きの前兆｜後半のσ_LOTが前半の0.5倍未満）",u"規則的に上下を繰り返している（振動｜上下交互が14点以上連続）"
cf,cg,ch,ci,cj,ck,cl=u"大きく外れた点がある（突発異常｜CL±6σ_LOTを超過｜過去30日）",u"値が一方向に動き続けている（トレンド｜同方向に6点以上連続｜過去30日）",u"中心から片側にずれ続けている（CLの同じ側に9点以上連続｜過去30日）",u"変動が大きくなってきている（不安定化｜後半のσ_LOTが前半の1.8倍超｜過去30日）",u"値がほとんど動いていない（貼り付き｜CL±1σ_LOT内に15点以上連続｜過去30日）",u"変動が小さくなってきている（貼り付きの前兆｜後半のσ_LOTが前半の0.5倍未満｜過去30日）",u"規則的に上下を繰り返している（振動｜上下交互が14点以上連続｜過去30日）"   #★変更4
#===== ★変更4 ここまで =====
def cm(bu):
    ey=bu["sd"]
    if ey is None or abs(ey)<max(1e-12,abs(bu["cl"])*1e-9): return None   # σ≒0は判定不能として除外（0割で|Z|爆発）
    return (bu["v"]-bu["cl"])/ey
def me(l):   # 中央値（案1のロバスト化に使用）
    l=sorted(l); k=len(l)
    return 0.0 if k==0 else (l[k//2] if k%2 else (l[k//2-1]+l[k//2])/2.0)
def cp(cq,cr=True,cs=True):
    ct={}; cu=[cm(bu) for bu in cq]; cv=[bu["v"] for bu in cq]
    if cr:   # 突発異常：判定は CL±6σ_LOT の比較のみ（割り算しないのでσ≒0でも爆発しない）
        jf=me([abs(bu["v"]) for bu in cq if bu["v"] is not None])   # 系列の代表スケール（CL≒0項目の保険）
        cw=[]
        for bu in cq:
            ex=bu["cl"]; ey=bu["sd"]
            if ex is None or ey is None: continue
            jg=abs(bu["v"]-ex)
            if jg>6*abs(ey):                     # 管理限界を実際に超えた点だけ
                jh=max(abs(ex),jf)               # 程度の分母は物理量（CL or 系列規模）。0へ潰れない
                cw.append(100.0*jg/jh if jh>0 else jg)   # 程度=乖離率%（分母不能時は乖離実数）
        if cw: ct[cf]=max(cw)
    if not cs: return ct
    cy=cz=1; da=0   # トレンド：連続同方向≥6
    for db in range(1,len(cv)): dc=(cv[db]>cv[db-1])-(cv[db]<cv[db-1]); cy=cy+1 if (dc!=0 and dc==da) else 1; da=dc; cz=max(cz,cy)
    if cz>=6: ct[cg]=cz
    dd=de=df=0   # 片側シフト：同符号連続≥9
    for cx in cu:
        if cx is None: dd=de=0; continue
        if cx>0: dd+=1; de=0
        elif cx<0: de+=1; dd=0
        else: dd=de=0
        df=max(df,dd,de)
    if df>=9: ct[ch]=df
    cy=dg=0   # 貼り付き：|z|<1連続≥15
    for cx in cu: cy=cy+1 if (cx is not None and abs(cx)<1) else 0; dg=max(dg,cy)
    if dg>=15: ct[cj]=dg
    dh=1; di=0; dj=0   # 振動：交互連続≥14
    for db in range(1,len(cv)):
        dc=1 if cv[db]>cv[db-1] else (-1 if cv[db]<cv[db-1] else 0)
        if dc==0: dh=1; di=0; continue
        dh=dh+1 if (di!=0 and dc==-di) else 1; di=dc; dj=max(dj,dh+1)
    if dj>=14: ct[cl]=dj
    if len(cq)>=8:   # 変動拡大/縮小：前半後半のσ_LOT平均を比較。BUG?:点少で過敏
        dk=len(cq)//2
        dl=[cq[db]["sd"] for db in range(dk) if cq[db]["sd"] not in (None,0)]
        dm=[cq[db]["sd"] for db in range(dk,len(cq)) if cq[db]["sd"] not in (None,0)]
        if dl and dm:
            dl=sum(dl)/len(dl); dm=sum(dm)/len(dm)   # 前半/後半の平均σ_LOT
            if dl>0 and dm>dl*1.8: ct[ci]=dm/dl
            if dl>0 and dm<dl*0.5: ct[ck]=(dl/dm if dm>0 else 99.0)
    return ct
dn={cf:u"%",cg:u"点連続",ch:u"点連続",cj:u"点連続",cl:u"点",ci:u"倍",ck:u"倍"}
do=[cf,cg,ch,ci,cj,ck,cl]

# ┌─【区分】JPEGエンコーダ ────────────────────────────────────────────
# │ dp=JPEGエンコーダ   dr=品質パラメータ(yで指定した品質)
# └──────────────────────────────────────────────────────────────────────────
dp=[dq for dq in ImageCodecInfo.GetImageEncoders() if dq.FormatID==ImageFormat.Jpeg.Guid][0]
dr=EncoderParameters(1); dr.Param[0]=EncoderParameter(Encoder.Quality,y)

# ┌─【区分】前回状態の読み込みと今回用の入れもの ──────────────────────────
# │ ds=前回状態(key→状態文字列)   dt=読み込んだ生テキスト   kb=解析できなかった行数
# │ ja()=状態のn番目→日時   jc=key→水位線   jx=前回“掲載された”keyの集合(前回サマリの母集合)
# │ jm=今回数えた最新加工日時(次回の水位線)   jl=今回の新規判定行数   ka=全期間の参考値[OK,NG]
# │ jr=診断カウンタ(skip=既報/old=移行窓/unk=未知判定値)   dv=今回の集計結果
# └──────────────────────────────────────────────────────────────────────────
ds={}   # 前回状態 prev[key]="OK;NG;係数;MA;継続回数;水位線;更新した実行時刻"   #▲修正2/7
#===== ▲修正13 ここから ===== 読み込みをV1/V2両対応にし、破損を握りつぶさず件数を出す
#★旧| try:
#★旧|     dt=a[aq]
#★旧|     if dt:
#★旧|         for du in dt.split(u"\n"):
#★旧|             if u"=" in du: cc,bt=du.rsplit(u"=",1); ds[cc]=bt
#★旧| except: ds={}
dt=kl(); kb=0
if dt is None:
    print "状態: 前回状態なし → 全keyを初回（全期間集計）として処理します"   #▲修正17
    print "      このため今回は母数が大きく、『新規発生』も多く出ます（異常ではありません）"
else:
    ds,kb=kr(dt)
    print "状態: 読込%d件 / 解析できなかった行%d / 元テキスト%d文字"%(len(ds),kb,len(dt))
    if kb: print "WARN 前回状態に壊れた行が%d行あります（容量超過による切り捨て・区切り文字の混入を疑ってください）"%kb
kc2=len([1 for cc in ds if bs(ds[cc]) is None])
if kc2: print "WARN OK/NG数として解釈できない状態が%d件あります（該当keyは悪化・改善の比較から外れます）"%kc2   #▲修正13
#===== ▲修正13 ここまで =====
if aj and an: ds={u"工程A|膜厚|STEP\x1f装置Ach1":u"40;2;3.0;30"}; print "TEST前回固定"
dv={}
#===== ▲修正2 ここから ===== 状態の6番目「水位線」7番目「更新した実行時刻」を読み出す
def ja(bt,db=5):   # 状態文字列のdb番目→DateTime。無い/壊れている場合はNone   #▲修正2
    try:
        bu=bt.split(u";")
        if len(bu)>db and bu[db].strip():
            bp=bu[db].strip()
            if len(bp)>=15 and bp.isdigit(): return DateTime(Int64.Parse(bp))   # 旧: .NET ticks   #▲修正13
            return k7(bp)                                                        # 新: base36秒   #▲修正13
    except: pass
    return None
jc={}   # key→水位線。これ以前の加工日時の行は「既に配信済み」として二度と数えない   #▲修正2
ep=None
for cc in ds:
    dc=ja(ds[cc],5)
    if dc is not None: jc[cc]=dc
    dc=ja(ds[cc],6)
    if dc is not None and (ep is None or dc>ep): ep=dc   # 状態中の最大＝前回の実行時刻
# 前回サマリ(全体NG率・NGありch数)の母集合。状態をマージ保存するようにしたため、   #▲修正7
# 「ds全件」ではなく「前回の配信で実際に掲載されたkey」だけを前回値として扱う。
jx=set(cc for cc in ds if ja(ds[cc],6)==ep) if ep is not None else set(ds)   #▲修正7
jm={}; jl={}   # jm=今回数えた最新加工日時(次回の水位線) / jl=今回の新規判定行数   #▲修正2
ka={}          # key→[全期間OK,全期間NG]。グラフ(全期間表示)との突き合わせ用の参考値。判定には一切使わない   #▲修正14
jr={"skip":0,"old":0,"unk":0}   # 診断カウンタ   #▲修正10
print "DBG 前回状態=%d件 / 水位線あり=%d件 / 前回掲載=%d件 (%s)"%(len(ds),len(jc),len(jx),u"通常運転" if jc else u"初回or移行回")   #▲修正10
#===== ▲修正2 ここまで =====

#===== ★変更5 ここから ===== 診断用リスト ii=[] を追加／ib(30日TimeSpan)を新設
#★旧| dw=[]; dx=[]; dy=[]; dz=0; ea=0; eb=[]; ec={}; ed={}; jw=[]   # rows=(項目,NG,母数,率)/rh=key→{種類:程度}/us=集計/ur=画像
#★旧| di=TimeSpan(n,0,0,0)
dw=[]; dx=[]; dy=[]; dz=0; ea=0; eb=[]; ec={}; ed={}; jw=[]; ii=[]   # rows=(項目,NG,母数,率)/rh=key→{種類:程度}/us=集計/ur=画像   #★変更5
di=TimeSpan(n,0,0,0); ib=TimeSpan(ia,0,0,0)   # di=移行用フォールバック窓 / ib=ルール判定窓   #★変更5 #▲修正3
#===== ★変更5 ここまで =====
try: jq=a[i]        # 実行前の項目選択を退避
except: jq=None
# ┌─【区分】項目ループ：NG率の集計 ──────────────────────────────────────
# │ ee=今の項目   ef=σ係数   eg=移動平均N   eh=判定のある行の最新日時   eh0=全行の最新日時(頁の母集合)
# │ ej/er=装置ch   dc=加工日時   az=判定値   eo=キー(項目+ch)   jk=このkeyの水位線
# │ ek=項目内NG数  el=項目内母数  em=ch→NG数  en=ch→OK数  jt=除外ch(OK皆無かつNGあり)  eq=掲載ch
# │ ec=key→集計区分ラベル(前回以降/初回(全期間)/移行)   ji/je/jj=診断カウンタ
# └──────────────────────────────────────────────────────────────────────────
for ee in be:
    try:
        a[i]=ee; e(400)   # BUG?: Sleep短いと前項目値を読む
        try: ef=a[k]
        except: ef=u"?"
        try: eg=a[l]
        except: eg=u"?"
#===== ▲修正3 ここから ===== 基準日時の作成（集計の窓には使わない。診断と頁母集合のためだけ）
#★旧|         eh={}
#★旧|         for ei in av.GetRows(bi,bj):
#★旧|             ej=bi.CurrentValue; dc=bj.CurrentValue
#★旧|             if ej in (None,"") or dc is None: continue
#★旧|             if ej not in eh or dc>eh[ej]: eh[ej]=dc
        eh={}; eh0={}   # eh=判定のある行の最新(診断用) / eh0=全行の最新(トレリス頁の母集合)   #▲修正3
        for ei in av.GetRows(bh,bi,bj):
            ej=bi.CurrentValue; dc=bj.CurrentValue
            if ej in (None,"") or dc is None: continue
            if ej not in eh0 or dc>eh0[ej]: eh0[ej]=dc
            if bh.CurrentValue not in (None,""):
                if ej not in eh or dc>eh[ej]: eh[ej]=dc
#===== ▲修正3 ここまで =====
#===== ★追加6 ここから ===== ic=項目内の最新加工日時／ie=停止ch集合(C案)の算出
#★旧|         ic=None   # 項目内の最新加工日時＝停止判定の基準点
#★旧|         for er in eh:
#★旧|             if ic is None or eh[er]>ic: ic=eh[er]
#★旧|         ie=set(er for er in eh if ic is not None and eh[er]<ic.Subtract(di))   # C案:最新が窓より古いch=停止ch→全期間
# ▲修正4: 停止ch(ic/ie)の概念を廃止。ch相対の窓をやめたので「止まっているch」は
#          “全期間で数え直す対象”ではなく“今回は新規行が無い＝非掲載”として自然に落ちる。
#===== ★追加6 ここまで =====
#===== ▲修正3/5 ここから ===== NG率集計を「前回配信以降の新規行だけ」に変更＋判定値の表記ゆれ吸収
        ek=el=0; em={}; en={}
        ji=0; je=0; jj=0   # 診断:既報スキップ / 移行窓スキップ / 未知判定値   #▲修正10
        for ei in av.GetRows(bh,bi,bj):
            ej=bi.CurrentValue; dc=bj.CurrentValue
            if ej in (None,"") or dc is None: continue
            if dc>jd: continue                          # 未来日時(誤登録・時刻ズレ)は今回対象外   #▲修正3
            eo=bz(ee,ej)
#★旧|             if eo in ds:
#★旧|                 ep=eh.get(ej,None)
#★旧|                 if ep is None or dc<ep.Subtract(di): continue      ←ch相対の窓＝二重計上の原因
#===== ▲修正14 ここから ===== 判定値の読み取りを期間フィルタより前に出し、全期間の参考値を同じ1パスで取る
            az=bh.CurrentValue
            if az in (None,""): continue
            az=unicode(az).strip().upper()              # 前後空白・大小文字の揺れを吸収   #▲修正5
            if   az in (u"NG",u"ＮＧ",u"×",u"NG判定"): az=u"NG"
            elif az in (u"OK",u"ＯＫ",u"○",u"◯",u"OK判定"): az=u"OK"
            else: jj+=1; continue                       # OK/NGどちらでもない値は数えず件数だけ記録   #▲修正5
            ay=ka.get(eo)
            if ay is None: ay=[0,0]; ka[eo]=ay
            ay[1 if az==u"NG" else 0]+=1                # 全期間(参考値)。期間フィルタを一切かけない   #▲修正14
#===== ▲修正14 ここまで =====
            jk=jc.get(eo)
            if jb and jk is not None:
                if dc<=jk: ji+=1; continue              # ★既報行：ロット遡及で再取得されても数えない   #▲修正3
            elif eo in ds:
                if dc<jd.Subtract(di): je+=1; continue  # 水位線が無い既存key＝移行回。実行時刻からn日   #▲修正3
            # 上記いずれにも当たらない＝初登場key → 全期間（従来どおり）
            el+=1
            if az==u"NG": ek+=1; em[ej]=em.get(ej,0)+1
            else: en[ej]=en.get(ej,0)+1
            if eo not in jm or dc>jm[eo]: jm[eo]=dc      # 水位線は“実際に数えた行”だけで進める   #▲修正3
            jl[eo]=jl.get(eo,0)+1
        jr["skip"]+=ji; jr["old"]+=je; jr["unk"]+=jj
#===== ▲修正3/5 ここまで =====
        jt=set(er for er in (set(en)|set(em)) if en.get(er,0)==0 and em.get(er,0)>0)   # OK皆無かつNGありのchは全集計・画像から除外
        for er in jt: ek-=em.get(er,0); el-=em.get(er,0)   # 項目のNG率からも取り除く
        dw.append((ee,ek,el,100.0*ek/el if el else 0))
        eq=(set(en)|set(em))-jt
        for er in eq:
            eo=bz(ee,er)
            dv[eo]=u"%d;%d;%s;%s"%(en.get(er,0),em.get(er,0),ef,eg)
#===== ★変更8 ここから ===== 集計区分ラベル判定
#★旧|             ec[eo]=(u"直近%d日"%n) if eo in ds else u"全期間"
#★旧|             ec[eo]=(u"直近%d日"%n) if (eo in ds and er not in ie) else u"全期間"
            ec[eo]=u"前回以降" if eo in jc else ((u"移行(直近%d日)"%n) if eo in ds else u"初回(全期間)")   #▲修正9
#===== ★変更8 ここまで =====
        print "DBG %s: 新規判定行=%d / 既報スキップ=%d / 移行窓スキップ=%d / 未知判定値=%d / 掲載ch=%d(除外%d) / 判定ありch=%d(全ch=%d)"%(ee,el,ji,je,jj,len(eq),len(jt),len(eh),len(eh0))   #▲修正10
        # ┌─【区分】項目ループ：系列の収集とルール判定 ────────────────────────────
        # │ es=ロット単位かどうか   et=収集に使うカーソル一覧   ew=ロット集約バッファ
        # │ eu=ch→系列(日時,値,CL,σ)   ev=ch→ウエハ生系列   cq/fe=点列   fc=検出結果   ed=key→検出結果
        # │ ii=診断用の窓内点数   jo=画像を撮る対象ch(集計あり ∪ 検出あり)
        # │ 期間は実行時刻から ia 日の絶対窓。NG率の窓とは無関係
        # └──────────────────────────────────────────────────────────────────────────
        es=(ee not in t) if s=="lot" else (ee in t)
        et=[bi,bj,bk,bl,bm,bn]; eu={}; ev={}
        if es:
            ew={}
            for ei in av.GetRows(*et):
                er=bi.CurrentValue; dc=bj.CurrentValue
                if er in (None,"") or dc is None: continue
#===== ★追加9 ここから ===== ルール判定窓30日フィルタ(ロット単位の系列収集)
#★旧|                 ep=eh.get(er,None)
#★旧|                 if ep is not None and dc<ep.Subtract(ib): continue   # ch相対の30日窓
                if dc>jd or dc<jd.Subtract(ib): continue   # ルール判定窓:実行時刻から30日(絶対窓)   #▲修正6
#===== ★追加9 ここまで =====
                cv=bk.CurrentValue; ex=bl.CurrentValue; ey=bm.CurrentValue; ez=bn.CurrentValue
                if cv is None or ex is None or ez in (None,""): continue
                ay=ew.setdefault(er,{}).setdefault(ez,[0.0,0.0,0.0,0,None,0])
                ay[0]+=cv; ay[1]+=ex; ay[3]+=1
                if ey is not None: ay[2]+=ey; ay[5]+=1   # BUG?: 欠損σを0扱いで平均するとσが縮み|Z|が爆発
                if ay[4] is None or dc>ay[4]: ay[4]=dc
                ev.setdefault(er,[]).append((dc,cv,ex,ey))
            for er,fa in ew.items():
                eu[er]=[(ay[4],ay[0]/ay[3],ay[1]/ay[3],(ay[2]/ay[5] if ay[5] else None)) for ay in fa.values() if ay[3]>0]
        else:
            for ei in av.GetRows(*et):
                er=bi.CurrentValue; dc=bj.CurrentValue
                if er in (None,"") or dc is None: continue
#===== ★追加10 ここから ===== ルール判定窓30日フィルタ(ウエハ単位の系列収集)
#★旧|                 ep=eh.get(er,None)
#★旧|                 if ep is not None and dc<ep.Subtract(ib): continue
                if dc>jd or dc<jd.Subtract(ib): continue   # ルール判定窓:実行時刻から30日(絶対窓)   #▲修正6
#===== ★追加10 ここまで =====
                cv=bk.CurrentValue; ex=bl.CurrentValue; ey=bm.CurrentValue
                if cv is None or ex is None: continue
                eu.setdefault(er,[]).append((dc,cv,ex,ey))
        jo=set(eq)   # 描画対象ch＝今回集計あり ∪ ルール検出あり（下のループで追加）   #▲修正8
        for er,fb in eu.items():
            if er in jt: continue   # 除外ch（OK皆無かつNGあり）はルール判定もしない
            fb.sort(key=cd)
            cq=[{"v":ba[1],"cl":ba[2],"sd":ba[3]} for ba in fb]
#===== ★追加11 ここから ===== 診断:30日窓内の点数を記録
            ii.append(len(cq))   # 診断:30日窓内の点数   #★追加11
#===== ★追加11 ここまで =====
            if es:
                fc=cp(cq,False,True) if len(cq)>=u else {}
                fd=sorted(ev.get(er,[]),key=cd)
                fe=[{"v":ba[1],"cl":ba[2],"sd":ba[3]} for ba in fd]
                if len(fe)>=u: fc.update(cp(fe,True,False))
            else:
                fc=cp(cq,True,True) if len(cq)>=u else {}
            if fc: ed[bz(ee,er)]=fc; jo.add(er)   # 集計は無くても検出があるchは撮る   #▲修正8
        # ┌─【区分】項目ループ：グラフ画像の撮影 ──────────────────────────────────
        # │ ff=chの並び(頁の母集合)  jz=正規化ch名→実ch名  fi=トレリス  fj=頁数  fk=頁index  js=頁名  jp=元の表示頁
        # │ fl=この頁の装置ch   fm=表示用のch名   fo=画像ファイル名   ca=Bitmap   fn=Graphics
        # │ fp/fq=今回のOK/NG   fr=NG率   fs=画像ラベル   eb=画像台帳   jw=撮れなかったch   fh/dx=詳細HTMLの断片
        # └──────────────────────────────────────────────────────────────────────────
#===== ▲修正8 ここから ===== 描画対象を jo に一本化（集計あり ∪ ルール検出あり）
        if jo:
#★旧|         if eq:
            ff=sorted(eh0,key=lambda bp:(bp.replace(u"-",u"").replace(u"_",u"").replace(u" ",u"").lower(),bp))   # この項目の全ch=トレリス頁の母集合   #▲修正3
            jz={}
            for er in eh0: jz[jv(er)]=er   # 正規化ch名→実ch名（頁名の表記ゆれ吸収）   #▲修正8
            fh=[]; fi=bf.Trellis; fj=fi.PageCount or 1
            if fj!=len(ff): print "WARN 項目%s: トレリス頁数%d != 項目内ch数%d（頁が無いchは撮影不可）"%(ee,fj,len(ff))
            try: jp=fi.ActivePageIndex   # 実行前のトレリス表示頁を退避
            except: jp=None
            for fk in range(fj):
                fi.ActivePageIndex=fk; e(200)
                try: js=unicode(fi.CurrentPage.Name)   # 実名が取れるならそれを最優先（並び順に依存しない）
                except:
                    try: js=unicode(fi.Pages[fk].Name)
                    except: js=None
#★旧|                 fl=js if (js is not None and js in eq) else (ff[fk] if fk<len(ff) else None)
                fl=None
                if js is not None: fl=js if js in eh0 else jz.get(jv(js))   # 掲載対象外のchも含め全chで解決   #▲修正8
                if fl is None:
                    fl=ff[fk] if fk<len(ff) else None
                    print "WARN 頁名でch解決不可→位置で代用: 項目%s 頁%d(%r)"%(ee,fk,js)
#★旧|                 if ak and (fl is None or (fl not in eq and bz(ee,fl) not in ed)): continue
                if ak and (fl is None or fl not in jo): continue   # 集計対象 or ルール検出chだけ描画   #▲修正8
#===== ▲修正8 ここまで =====
                if ak and al:
                    eo=bz(ee,fl)
#===== ★変更12 ここから ===== 差分スキップ比較を先頭4フィールドに限定(状態5フィールド化に伴う回帰修正)
#★旧|                     if ds.get(eo)==dv.get(eo): ea+=1; continue
                    if u";".join((ds.get(eo) or u"").split(u";")[:4])==dv.get(eo): ea+=1; continue   # 5番目以降(継続回数/水位線)は比較対象外   #★変更12
#===== ★変更12 ここまで =====
                fm=fl if fl is not None else u"page %d"%(fk+1)
                try:   # 1chの失敗で残chを巻き込まない
                    fi.ActivePageIndex=fk; e(900)   # BUG?: 待ち不足だと前ページの絵を撮る（ラベルと画像がズレる）
                    ca=Bitmap(w,x); fn=Graphics.FromImage(ca); fn.Clear(Color.White)   # BUG?: Clear無で余白黒
                    fn.TextRenderingHint=fn.TextRenderingHint.AntiAlias
                    bf.Render(fn,Rectangle(0,0,w,x))
                    fo=bq(u"%s__%s.jpg"%(ee,fm))
                    ca.Save(d(au,fo),dp,dr); ca.Dispose(); fn.Dispose(); dz+=1
                except Exception as bb:
                    dy.append(u"%s/%s(描画): %s"%(ee,fm,bb)); continue
                if fl is not None:
                    eo=bz(ee,fl); fp=en.get(fl,0); fq=em.get(fl,0); fr=bv(fp,fq)
#===== ▲修正9 ここから ===== 新規データが無いchのラベルを「OK 0・NG 0」ではなく明示表記に
                    if jl.get(eo,0)>0:
                        fs=u'%s ／ %s ／ <span style="color:green">OK %d</span> ・ <span style="color:#c0392b">NG %d</span> ・ 母数 %d ／ NG率 %.2f%% ／ <span style="color:#888">[%s]</span>'%(bo(ee),bo(fm),fp,fq,fp+fq,fr,ec.get(eo,u"初回(全期間)"))
                    else:
                        fs=u'%s ／ %s ／ <span style="color:#888">今回の新規データなし（推移パターン検出のため掲載）</span>'%(bo(ee),bo(fm))
#===== ▲修正9 ここまで =====
#===== ▲修正14 ここから ===== グラフ1枚ごとに「全期間の同じ集計」を毎回併記（参考値・判定には不使用）
                    ay=ka.get(eo,[0,0])
                    fs+=u'<br><span style="color:#666;font-weight:normal">全期間（このグラフ全体・参考値／集計や判定には使用していません）：OK %d ・ NG %d ・ 母数 %d ／ NG率 %.2f%%</span>'%(ay[0],ay[1],ay[0]+ay[1],bv(ay[0],ay[1]))   #▲修正14
#===== ▲修正14 ここまで =====
                    eb.append((fr,ee,fl,fp,fq,d(au,fo),fo))
                else: fs=u"%s ／ %s"%(bo(ee),bo(fm))
                fh.append(u'<p class="lbl">%s</p><img src="img/%s"/>'%(fs,bo(fo)))
            if jp is not None:   # 実行後にトレリス表示頁を元へ戻す
                try: fi.ActivePageIndex=jp
                except: pass
            for er in jo:        # 画像が撮れなかったchを記録（頁数不足の検知）
                if not [1 for ba in eb if ba[1]==ee and ba[2]==er]: jw.append(bz(ee,er))
            if fh: dx.append(u'<section><h2>%s</h2><p class="m">NG %d / %d ＝ %.2f%%</p>%s</section>'%(bo(ee),ek,el,dw[-1][3],u"".join(fh)))
    except Exception as bb: dy.append(u"%s: %s"%(ee,bb))
if jq is not None:   # 実行後に項目選択を元へ戻す
    try: a[i]=jq; e(400)
    except: pass
#===== ★追加13 ここから ===== ルール継続回数の算出と状態5番目への保存(ik/ij/ig/ih/im)
# --- ルール検出の継続回数（状態の5番目のフィールドに保存） ---   #★追加13
# ┌─【区分】ルール検出の継続回数 ──────────────────────────────────────────
# │ ik=ルール名→番号   ij()=状態の5番目→継続回数の辞書   ig=前回の継続回数   ih=今回の継続回数
# │ im()=表示用の「新規／継続N回目」   検出が続いた“配信回数”を数える（週数ではない）
# └──────────────────────────────────────────────────────────────────────────
ik={}   #★追加13
for db,gq in enumerate(do): ik[gq]=db   # ルール名→インデックス（名称変更に強い）   #★追加13
def ij(bt):   # 状態文字列の5番目「idx:回数,...」を辞書に   #★追加13
    ct={}   #★追加13
    try:   #★追加13
        bu=bt.split(u";")   #★追加13
        if len(bu)>4 and bu[4]:   #★追加13
            for ba in bu[4].split(u","):   #★追加13
                if u":" in ba:   #★追加13
                    cc2,az2=ba.split(u":",1); ct[int(cc2)]=int(az2)   #★追加13
    except: pass   #★追加13
    return ct   #★追加13
ig={}   #★追加13
for cc in ds: ig[cc]=ij(ds[cc])   # 前回の継続回数   #★追加13
ih={}   #★追加13
#★旧| for cc in dv:
for cc in (set(dv)|set(ed)|set(ds)):   # 今回集計が無くても検出があるkeyの継続回数を進める   #▲修正7
    fy=ed.get(cc,{}); ax=ig.get(cc,{}); bd={}   #★追加13
    for gq in fy:   #★追加13
        if gq in ik: bd[ik[gq]]=ax.get(ik[gq],0)+1   # 前回も出ていれば+1、無ければ1(=新規)   #★追加13
    ih[cc]=bd   #★追加13
#★旧|     dv[cc]=dv[cc]+u";"+(u",".join(u"%d:%d"%(db,bd[db]) for db in sorted(bd)) if bd else u"")
#  ▲修正7: dvは「今回の集計値(4フィールド)」のまま保持し、保存用の文字列は jy() で組み立てる。
#          こうしないと dv を参照する後段（bs/悪化/改善）と保存形式が絡んで壊れやすい。
def im(cc,gq):   # 表示用「新規／継続N回目」   #★追加13
    db=ih.get(cc,{}).get(ik.get(gq,-1),1)   #★追加13
    return u"新規" if db<=1 else u"継続%d回目"%db   #★追加13
   #★追加13
#===== ★追加13 ここまで =====
#===== ▲修正7 ここから ===== 状態は「上書き」ではなく「マージ」保存
# 旧実装は dv（今回集計できたkeyだけ）で丸ごと上書きしていたため、
#   ・今回新規データが無かったkeyの水位線・継続回数・前回値が消える
#   ・翌週そのkeyが「初登場」に戻り、全期間集計で先週と同じ数字が再浮上する
# という失敗/成功が隔週で入れ替わる挙動になっていた。ここでマージして持ち越す。
# ┌─【区分】状態の直列化と確定 ────────────────────────────────────────────
# │ jy()=1keyぶんの状態文字列を組み立てる   jn=マージ後の状態辞書(掲載されなかったkeyも持ち越す)
# │ kv=保存するテキスト   kn=採用件数   kf=失効で捨てた件数   kq()=実際に保存する（配信成功後に呼ぶ）
# └──────────────────────────────────────────────────────────────────────────
def jy(cc):   # 保存用の状態文字列 "OK;NG;係数;MA;継続回数;水位線ticks;更新した実行時刻ticks"   #▲修正7
    bu=(jn.get(cc) or u"").split(u";")
    while len(bu)<7: bu.append(u"")
    if cc in dv:
        bu2=dv[cc].split(u";")
        bu[0],bu[1],bu[2],bu[3]=bu2[0],bu2[1],bu2[2],bu2[3]   # 今回集計できたkeyだけ数値を更新
        bu[6]=u"%d"%jd.Ticks                                  # 今回の配信で掲載したkeyの印
    bd=ih.get(cc,{})
    bu[4]=u",".join(u"%d:%d"%(db,bd[db]) for db in sorted(bd)) if bd else u""
    if cc in jm: bu[5]=k6(jm[cc])                             # 水位線は今回数えた最新加工日時へ前進   #▲修正13
    return u";".join(bu[:7])
jn=dict(ds)
for cc in (set(ds)|set(dv)): jn[cc]=jy(cc)
#===== ▲修正15 ここから ===== 直列化だけ先に済ませ、実際の書き込みは配信が成功してから行う
#★旧| if not (aj and ao):
#★旧|     a[aq]=u"\n".join(u"%s=%s"%(cc,az) for cc,az in jn.items())
#  なぜ分けるか: 状態を先に書くと、メール送信に失敗した週の行が「集計済み」として記録され、
#  その週のNG・悪化・新規が二度と報告されなくなる。配信の成功を確認してから確定させる。
kv,kn,kf=kw(jn)   # kv=保存するテキスト / kn=採用件数 / kf=失効で捨てた件数   #▲修正15
print "DBG 状態: 保存予定%d件（今回更新%d / 持ち越し%d / 失効破棄%d）／ %d文字"%(kn,len(dv),kn-len(dv),kf,len(kv))   #▲修正15
def kq():   # 状態の確定（配信が成立した後にだけ呼ぶ）   #▲修正15
    if aj and not ao:
        print "TEST実行のため状態は保存しません（保存したい場合は ao=True）"; return   #▲修正12
    bp=kp(kv)
    if bp in (u"保存先なし",u"保存失敗"): print "状態: 保存できませんでした（%s）"%bp   #▲修正17
    else: print "状態を保存しました → %s / %d件 %d文字"%(bp,kn,len(kv))
#===== ▲修正15 ここまで =====
#===== ▲修正7 ここまで =====

# ┌─【区分】画像台帳とランキングの組み立て ────────────────────────────────
# │ ft=key→画像   ju=正規化key→画像   fx=今回の全key(率,項目,ch,OK,NG,key)
# │ fz/ga/gb=全体の母数/NG/率   gc=NGのあったch数   gd/ge/gf/gh=前回の同じ値
# │ gi=悪化   gk=NG率トップ   gl=一覧表   gm=新規発生   gn=改善   gp=ルール種類別トップ   gs()=推移特徴の文字列
# └──────────────────────────────────────────────────────────────────────────
ft={}; ju={}
#★旧| def jv(cc): ...   ←▲修正8で定義を前倒し（トレリス頁名の解決にも使うため）
for fr,fu,fv,fp,fq,fw,fo in eb:
    ft[bz(fu,fv)]=(fw,fo); ju[jv(bz(fu,fv))]=(fw,fo)
fx=[]   # cu2=(率,項目,ch,OK,NG,key)
for cc in dv:
    fy=bs(dv[cc])
    if fy is None: continue
    fu,fv=cb(cc); fx.append((bv(fy[0],fy[1]),fu,fv,fy[0],fy[1],cc))
fz=sum(by for db,bd,by,fr in dw); ga=sum(bd for db,bd,by,fr in dw)
gb=100.0*ga/fz if fz else 0
gc=len([1 for ej in fx if ej[4]>0])
gd=ge=gf=0
#★旧| for cc in ds:
for cc in jx:   # 前回“掲載された”keyだけを前回値として集計（状態マージで全履歴が混ざるのを防ぐ）   #▲修正7
    gg=bs(ds[cc])
    if gg: gd+=gg[0]; ge+=gg[1]; gf+=1 if gg[1]>0 else 0
gh=100.0*ge/(gd+ge) if (gd+ge) else 0
gi=[]   # (Δ,項目,ch,OK,NG,率,前率,key) 係数/MA変化時は基準変更→除外
for fr,fu,fv,fp,fq,cc in fx:
    gg=bs(ds[cc]) if ds.get(cc) else None; fy=bs(dv[cc])
    if gg is None or fy is None or gg[2]!=fy[2] or gg[3]!=fy[3]: continue
    ax=bv(gg[0],gg[1]); gj=fr-ax
    if gj>0: gi.append((gj,fu,fv,fp,fq,fr,ax,cc))
gi.sort(key=cd,reverse=True); gi=gi[:af]
gk=sorted(fx,key=cd,reverse=True)[:ag]
#===== ★変更14 ここから ===== 一覧表の掲載条件を「NG>0 または ルール検出あり」に
#★旧| gl=sorted([ej for ej in fx if ej[4]>0 and ej[0]>=ai],key=cd,reverse=True)
gl=sorted([ej for ej in fx if (ej[4]>0 and ej[0]>=ai) or ej[5] in ed],key=cd,reverse=True)   # NG>0 または ルール検出あり   #★変更14
#===== ★変更14 ここまで =====
gm=[]
for cc in dv:
    fy=bs(dv[cc]) if cc not in ds else None
    if fy and fy[1]>0: fu,fv=cb(cc); gm.append((bv(fy[0],fy[1]),fu,fv,fy[0],fy[1]))
gm.sort(key=cd,reverse=True); gm=gm[:ah]
gn=[]   # 改善は全件（絞らない）
for cc in dv:
    if cc in ds:
        gg=bs(ds[cc]); fy=bs(dv[cc])
        if gg is None or fy is None or gg[2]!=fy[2] or gg[3]!=fy[3]: continue
        ax=bv(gg[0],gg[1]); go=bv(fy[0],fy[1]); gj=go-ax
        if gj<0: fu,fv=cb(cc); gn.append((gj,fu,fv,go,ax))
gn.sort(key=cd)
gp={}   # ルール種類ごと程度順トップN
for eo,fc in ed.items():
    fu,fv=cb(eo)
    for gq,gr in fc.items(): gp.setdefault(gq,[]).append((gr,fu,fv,eo))
for gq in gp:
    gp[gq]=sorted(gp[gq],key=cd,reverse=True)[:v]
def gs(eo):
    fc=ed.get(eo)
    if not fc: return u""
    gt=[]
    for gq in do:
        if gq in fc:
            gu=dn.get(gq,u""); gv=fc[gq]
#===== ★変更15 ここから ===== gs():推移特徴に「新規/継続N回目」を併記＋到達不能だったσ分岐を除去
#★旧|             gt.append(u"%s（%.1f%s）"%(gq,gv,gu) if gu in (u"σ",u"倍") else u"%s（%d%s）"%(gq,int(gv),gu))
            gt.append(u"%s（%.1f%s・%s）"%(gq,gv,gu,im(eo,gq)) if gu in (u"倍",) else u"%s（%d%s・%s）"%(gq,int(gv),gu,im(eo,gq)))   #★変更15
#===== ★変更15 ここまで =====
    return u" / ".join(gt)

# ┌─【区分】メール本文の組み立て ──────────────────────────────────────────
# │ gw(画像srcを返す関数)=本文HTML   gy()=画像タグ   hb()=セル   hc()=行   he()=箇条書き   hg()=見出し+一覧+画像
# │ dk=本文を組み立てていく文字列   hj=表の順位   hm=画像の通番   kz=スクリプト版数   ky=コード差分
# │ プレビューは hr()（相対パス）、送信時は hv()（cid埋め込み）を渡して同じ関数を使い回す
# └──────────────────────────────────────────────────────────────────────────
def gw(gx):
    def gy(cc,gz):
        ha=ft.get(cc) or ju.get(jv(cc))   # 完全一致→表記ゆれ吸収の順で引く
        return (u'<img src="%s" style="max-width:600px"><br>'%gx(ha[1],ha[0],gz)) if ha else u'<p>（画像なし・詳細は添付zip参照）</p>'
    def hb(ba): return u'<td style="border:1px solid #999">%s</td>'%ba
#===== ★変更16 ここから ===== hc():行の背景色を指定できるよう引数を追加
#★旧|     def hc(hd): return u'<tr>'+u''.join(hb(dq) for dq in hd)+u'</tr>'
    def hc(hd,ba=u""): return (u'<tr style="background:#fff8e1">' if ba else u'<tr>')+u''.join(hb(dq) for dq in hd)+u'</tr>'   #★変更16
#===== ★変更16 ここまで =====
    def he(fb,hf): return (u'<ul>'+u''.join(hf(ba) for ba in fb)+u'</ul>') if fb else ce
    def hg(hh,fb,hf,hi):
        dk=u'<p><b>%s</b></p>'%hh
        if not fb: return dk+ce
        for db,ba in enumerate(fb,1): dk+=hf(ba)+gy(ba[-1],u"%s%d"%(hi,db))
        return dk
#===== ★変更17 ここから ===== 本文タイトルを「トピックス」に変更／期間の注意書きを新仕様に差替
#★旧|     dk=u'<html><body style="font-family:Meiryo;font-size:14px"><h2>SPC 日次トピックス</h2>'
#★旧|     dk+=u'<p ...>【集計期間について】既存の装置chは「最新加工日時から直近%d日」、今回初めて登場した装置chは「全期間」で集計しています。...</p>'%n
#★旧|     dk+=u'<p ...>【期間について】<b>NG率・悪化・改善・新規</b>＝そのchの最新加工日時から直近%d日（...）。...</p>'%(n,n,ia,ia)
    dk=u'<html><body style="font-family:Meiryo;font-size:14px"><h2>トピックス</h2>'   #★変更17
    dk+=u'<p style="background:#fff8e1;border-left:4px solid #f0ad4e;padding:6px 10px">【期間について】<b>NG率・悪化・改善・新規</b>＝<b>前回配信以降に新しく追加された加工日時のデータだけ</b>を集計しています（初登場の装置chのみ全期間。下表「集計」欄を参照）。ロット単位の抽出により先々週以前の工程データが再び取り込まれても、<b>配信済みの分は二重計上しません</b>（今回新規データが無い装置chは掲載されません）。<b>推移パターンの判定</b>＝実行日から直近%d日。%d日窓から外れた検出は自動的に消えます（「新規／継続N回目」を併記）。<b>グラフ画像</b>＝全期間表示のため、上記の期間とは一致しません。</p>'%(ia,ia)   #▲修正9
#===== ★変更17 ここまで =====
    dk+=u'<p><b>■全体サマリ</b><br>全体NG率：%.2f%%（前回 %.2f%%）／ NGのあった装置ch：%d（前回 %d）</p>'%(gb,gh,gc,gf)
    dk+=hg(u'■悪化幅トップ%d（前回比でNG率が上がった装置ch）'%af,gi,lambda ba:u'<p><b>%s ／ %s</b>：OK %d ・ NG %d ・ 母数 %d ／ NG率 %.2f%%（前回 %.2f%% ／ +%.2f）</p>'%(bo(ba[1]),bo(ba[2]),ba[3],ba[4],ba[3]+ba[4],ba[5],ba[6],ba[0]),u"w")
    dk+=hg(u'■NG率トップ%d（絶対値・今回分）'%ag,gk,lambda ba:u'<p><b>%s ／ %s</b>：OK %d ・ NG %d ・ 母数 %d ／ NG率 %.2f%% ／ [%s]</p>'%(bo(ba[1]),bo(ba[2]),ba[3],ba[4],ba[3]+ba[4],ba[0],ec.get(ba[5],u"")),u"t")
    dk+=u'<p><b>■NGのある全装置ch（NG率順・%d件）</b></p>'%len(gl)
    if gl:
        dk+=u'<table border="1" cellpadding="4" cellspacing="0" style="border-collapse:collapse;font-size:13px">'+hc((u'順位',u'項目',u'装置ch',u'OK',u'NG',u'母数',u'NG率',u'集計',u'推移の特徴'))
        hj=0
        for fr,fu,fv,fp,fq,cc in gl:
            hj+=1; hk=gs(cc); hl=bo(hk) if hk else u'<span style="color:#aaa">―</span>'
#===== ★変更18 ここから ===== 一覧表の検出行に背景色を適用
#★旧|             dk+=hc((hj,bo(fu),bo(fv),fp,fq,fp+fq,u'%.2f%%'%fr,ec.get(cc,u""),hl))
            dk+=hc((hj,bo(fu),bo(fv),fp,fq,fp+fq,u'%.2f%%'%fr,ec.get(cc,u""),hl),hk)   #★変更18
#===== ★変更18 ここまで =====
        dk+=u'</table>'
    else: dk+=ce
    dk+=u'<p><b>■新規発生（前回に無く今回NGが出た装置ch）トップ%d</b></p>'%ah+he(gm,lambda ba:u'<li>%s ／ %s：NG率 %.2f%%（OK %d ・ NG %d）［全期間集計］</li>'%(bo(ba[1]),bo(ba[2]),ba[0],ba[3],ba[4]))
    dk+=u'<p><b>■改善（前回比でNG率が下がった装置ch）全%d件</b></p>'%len(gn)+he(gn,lambda ba:u'<li>%s ／ %s：NG率 %.2f%% ←前回 %.2f%%（%.2f）</li>'%(bo(ba[1]),bo(ba[2]),ba[3],ba[4],ba[0]))
    dk+=u'<hr><h3>■推移パターン別の注目装置ch（種類ごと程度順トップ%d）</h3>'%v
    hm=0
    for gq in do:
        fb=gp.get(gq,[])
        gu=dn.get(gq,u"")
        dk+=u'<p style="background:#eef;padding:4px 8px;font-weight:bold">%s（%d件）</p>'%(bo(gq),len(fb))
        if not fb: dk+=ce; continue   # 該当なしも明記（伏せない）
        for gr,fu,fv,cc in fb:
#===== ★変更19 ここから ===== ルール別トピックスに「新規/継続N回目」を併記＋σ分岐を除去
#★旧|             hm+=1; ey=u"%.1f%s"%(gr,gu) if gu in (u"σ",u"倍") else u"%d%s"%(int(gr),gu)
#★旧|             dk+=u'<p><b>%s ／ %s</b>：程度 %s</p>'%(bo(fu),bo(fv),ey)+gy(cc,u"r%d"%hm)
            hm+=1; ey=u"%.1f%s"%(gr,gu) if gu in (u"倍",) else u"%d%s"%(int(gr),gu)   #★変更19
            dk+=u'<p><b>%s ／ %s</b>：程度 %s ／ <span style="color:#c0392b">%s</span></p>'%(bo(fu),bo(fv),ey,im(cc,gq))+gy(cc,u"r%d"%hm)   #★変更19
#===== ★変更19 ここまで =====
    dk+=u'<hr><p>全項目・全画像の詳細は、添付zip内の ng_report.html をご覧ください。</p>'
#===== ▲追加16 ここから ===== 末尾に版数を明記（どのコードが出した数字かを配信物だけで追える）
    dk+=u'<p style="color:#888;font-size:12px">スクリプト %s ／ 実行 %s%s</p>'%(
        bo(kz),jd.ToString("yyyy-MM-dd HH:mm"),
        u' ／ <b>コード変更あり</b>：差分は添付zip内の code_diff.txt' if ky else u"")   #▲追加16
#===== ▲追加16 ここまで =====
    dk+=u'</body></html>'
    return dk

# ┌─【区分】詳細HTMLとCSVの出力 ────────────────────────────────────
# │ hn=項目別サマリの表   ho=CSS   hp=詳細HTML全体   hq=書き込みStreamWriter
# │ ng_report.html=詳細  ng_summary.csv=集計(Shift_JIS)  mail_body_preview.html=本文プレビュー
# └──────────────────────────────────────────────────────────────────────────
hn=u"".join(u"<tr><td>%s</td><td>%d</td><td>%d</td><td>%.2f%%</td></tr>"%(bo(db),bd,by,fr) for db,bd,by,fr in dw)
#===== ★変更20 ここから ===== 詳細HTMLのh1／期間注意書き／CSSの%%→%(既知バグ修正)
#★旧| ho=(... u'img{max-width:100%%;...')   # BUG?: %は%%必須
#★旧| hp=(u'...<p class="note">【期間】NG率＝直近%d日（初登場ch・停止chは全期間...）。推移パターン判定＝直近%d日。...</p>'
ho=(u'body{font-family:Meiryo;margin:32px}h2{background:#f0f3f7;padding:8px 12px;border-left:6px solid #c0392b}'u'.m{color:#c0392b;font-weight:bold}.lbl{font-weight:bold;background:#eef;padding:3px 8px;margin:12px 0 2px;border-left:4px solid #36c}'u'.note{background:#fff8e1;border-left:4px solid #f0ad4e;padding:6px 10px}'u'img{max-width:100%;border:1px solid #ccc}section{page-break-inside:avoid}table{border-collapse:collapse}td,th{border:1px solid #999;padding:4px 10px}')   # 注: hoは%書式の引数として渡すため、%はエスケープ不要（旧版の%%は無効CSSだった）   #★変更20
hp=(u'<!DOCTYPE html><meta charset="utf-8"><style>%s</style><h1>NG率レポート（自動配信）</h1>'   #★変更20
 u'<p class="note">【期間】NG率＝<b>前回配信以降に追加された加工日時のデータのみ</b>（初登場chは全期間。画像ラベル末尾の [前回以降]／[初回(全期間)] で区別）。ロット遡及で再取得された配信済みデータは二重計上しません。推移パターン判定＝実行日から直近%d日。グラフ画像は全期間表示です。</p>'   #▲修正9
#===== ★変更20 ここまで =====
 u'<p>作成 %s ／ 失敗 %d 件 ／ 画像 %d 枚 ／ 差分スキップ %d 件 ／ スクリプト %s</p>'   #▲追加16
 u'<table><tr><th>項目</th><th>NG数</th><th>母数</th><th>NG率</th></tr>%s</table>%s%s'
#===== ★変更21 ここから ===== 詳細HTMLの書式引数
#★旧|  %(ho,n,n,DateTime.Now.ToString("yyyy-MM-dd HH:mm"),len(dy),dz,ea,hn,u"".join(dx),
#★旧|  %(ho,n,n,ia,DateTime.Now.ToString("yyyy-MM-dd HH:mm"),len(dy),dz,ea,hn,u"".join(dx),
 %(ho,ia,jd.ToString("yyyy-MM-dd HH:mm"),len(dy),dz,ea,bo(kz),hn,u"".join(dx),   #▲修正9 #▲追加16
#===== ★変更21 ここまで =====
   (u"<h2>失敗</h2><pre>"+bo(u"\n".join(dy))+u"</pre>") if dy else u""))
hq=StreamWriter(d(at,"ng_report.html"),False,Encoding.UTF8); hq.Write(hp); hq.Close()

hq=StreamWriter(d(at,"ng_summary.csv"),False,Encoding.GetEncoding("shift_jis"))
#★旧| hq.WriteLine("項目,装置ch,OK,NG,NG率(%),集計")
hq.WriteLine("項目,装置ch,OK,NG,NG率(%),集計,全期間OK,全期間NG,全期間NG率(%)")   #▲修正14
for cc in dv:
    fy=bs(dv[cc])
    if fy is None: continue
    fu,fv=cb(cc); ay=ka.get(cc,[0,0])
    hq.WriteLine(u"%s,%s,%d,%d,%.2f,%s,%d,%d,%.2f"%(fu,fv,fy[0],fy[1],bv(fy[0],fy[1]),ec.get(cc,u""),ay[0],ay[1],bv(ay[0],ay[1])))   #▲修正14
hq.Close()

def hr(fo,fw,hs): return u"img/"+bo(fo)
print "DBG 画像台帳ft=%d件 / eb=%d件"%(len(ft),len(eb))
if ft: print "DBG ft キー例:",repr(sorted(ft)[0])
for ba in gk[:3]: print "DBG NG率トップ key=%r 完全一致=%s 正規化一致=%s"%(ba[5],ba[5] in ft,jv(ba[5]) in ju)
for gq in do:
    for ba in gp.get(gq,[])[:2]: print "DBG ルール key=%r → ftにある=%s"%(ba[3],ba[3] in ft)
hq=StreamWriter(d(at,"mail_body_preview.html"),False,Encoding.UTF8); hq.Write(gw(hr)); hq.Close()

# ┌─【区分】zipの作成と診断出力 ────────────────────────────────────────
# │ ht=zipのパス（実行フォルダの外に作る。中に作ると自分を固めて失敗する）
# │ 以降のprintは実行ログ用。既報スキップ・未知判定値・窓内点数の分布などの健全性指標を出す
# └──────────────────────────────────────────────────────────────────────────
# zip（baseの外に作る）  BUG?: base内に作ると自分を固め使用中エラー
#★旧| ht=d(ar,"ng_report_%s.zip"%DateTime.Now.ToString("yyyyMMdd_HHmm"))
ht=d(ar,"ng_report_%s.zip"%jd.ToString("yyyyMMdd_HHmm"))   #▲修正1
if File.Exists(ht): File.Delete(ht)
e(300); ZipFile.CreateFromDirectory(at,ht)

print "=== 完了 ==="
#===== ★変更22 ここから ===== 完了ログの期間表示を新仕様に差替
#★旧| print "集計: 既存ch=直近%d日 / 初回ch=全期間"%n
#★旧| print "集計: NG率=直近%d日(初回/停止ch=全期間) / ルール判定=直近%d日"%(n,ia)
print "集計: NG率=前回配信以降の新規行のみ(初回ch=全期間 / 水位線なしkeyは移行として直近%d日) / ルール判定=実行時刻から直近%d日"%(n,ia)   #▲修正9
#===== ★変更22 ここまで =====
print "zip:",ht
print "画像%d / 差分skip%d / 失敗%d"%(dz,ea,len(dy))
print "DBG 集計ch総数=%d / 画像=%d"%(len(dv),dz)
print "画像未取得ch=%d件"%len(jw)
#===== ▲修正10 ここから ===== 二重計上対策の診断
print "DBG 既報スキップ=%d行 / 移行窓スキップ=%d行 / 未知判定値=%d行"%(jr["skip"],jr["old"],jr["unk"])   #▲修正10
print "DBG 水位線を更新したkey=%d件（次回はこの加工日時より後の行だけを集計）"%len(jm)   #▲修正10
if jr["unk"]: print "WARN 判定列にOK/NG以外の値が%d行あります（列指定または表記の確認を推奨）"%jr["unk"]   #▲修正10
#===== ▲修正10 ここまで =====
#===== ★追加23 ここから ===== 診断print(窓内点数の分布・ゲート未達件数・各ルールの点数到達率)
if ii:   #★追加23
    ii.sort()   #★追加23
    print "DBG %d日窓内点数: 最小%d / 中央%d / 最大%d / 平均%.1f"%(ia,ii[0],ii[len(ii)//2],ii[-1],1.0*sum(ii)/len(ii))   #★追加23
    print "DBG ゲート%d点未満で判定不能: %d件 / 全%d系列"%(u,len([1 for ba in ii if ba<u]),len(ii))   #★追加23
    for ba,bd in ((6,u"トレンド"),(9,u"片側シフト"),(14,u"振動"),(15,u"貼り付き")):   #★追加23
        print "DBG   %s(%d点必要): 到達 %d系列 (%.0f%%)"%(bd,ba,len([1 for db in ii if db>=ba]),100.0*len([1 for db in ii if db>=ba])/len(ii))   #★追加23
#===== ★追加23 ここまで =====
for cc in jw[:5]: print "  未取得:",repr(cc)
print "悪化%d / トップ%d / 全NGch%d / 新規%d / 改善%d"%(len(gi),len(gk),len(gl),len(gm),len(gn))
if dy: print "FAIL0:",dy[0]

# ┌─【区分】メール送信と後始末 ────────────────────────────────────────────
# │ hu=埋め込み画像   hv()=cidを返す関数   hx=本文   co=MailMessage   hy=HTMLビュー   hz=添付zip
# │ 送信に成功したときだけ kq() で状態を確定し、実行フォルダとzipを削除する
# │ 失敗時は状態を保存せず成果物も残し、例外を送出してジョブを失敗扱いにする
# └──────────────────────────────────────────────────────────────────────────
# 送信（本番かつSEND_MAIL。TEST中は送らない二重ガード）
if (not aj) and am:
    from System.Net.Mail import MailMessage,SmtpClient,Attachment,MailAddress,AlternateView,LinkedResource
    from System.Net.Mime import MediaTypeNames
    hu=[]
    def hv(fo,fw,hs):
        hw=LinkedResource(fw,MediaTypeNames.Image.Jpeg); hw.ContentId=hs; hu.append(hw); return u"cid:"+hs
    hx=gw(hv)
    co=MailMessage(); co.From=MailAddress(z); co.To.Add(aa)
#===== ★変更24 ここから ===== メール件名を「NG率レポート（トピックス付き・自動配信）」に変更
#★旧|     co.Subject="SPC NG率レポート（トピックス付き・自動配信）"
    co.Subject="NG率レポート（トピックス付き・自動配信）"   #★変更24
#===== ★変更24 ここまで =====
    hy=AlternateView.CreateAlternateViewFromString(hx,None,MediaTypeNames.Text.Html)
    for hw in hu: hy.LinkedResources.Add(hw)
    co.AlternateViews.Add(hy); hz=Attachment(ht); co.Attachments.Add(hz)
#===== ▲修正15 ここから ===== 送信成功時だけ「状態の確定」と「成果物の削除」を行う
#★旧|     try: SmtpClient(ab,ac).Send(co)
#★旧|     finally:   # BUG?: 解放しないとファイル掴んで消せない
#★旧|         hz.Dispose(); co.Dispose()
#★旧|         try: Directory.Delete(at,True)
#★旧|         except: pass
#★旧|         try: File.Delete(ht)
#★旧|         except: pass
#  旧実装は finally で削除していたため、送信に失敗しても成果物が消え、再送も検証もできなかった。
    try:
        SmtpClient(ab,ac).Send(co)
    except Exception,bb:
        hz.Dispose(); co.Dispose()
        print "ERROR メール送信に失敗しました:",bb
        print "ERROR 状態は保存していません。この週の分は次回の実行で再集計されます"
        print "ERROR 成果物は削除せず残しました:",ht
        raise                                   # ジョブを失敗扱いにして気づけるようにする
    hz.Dispose(); co.Dispose()   # BUG?: 解放しないとファイル掴んで消せない
    kq()                         # ←配信が成立してから水位線を確定
    try: Directory.Delete(at,True)
    except: pass
    try: File.Delete(ht)
    except: pass
else:
    kq()                         # 送信しない構成（TEST/送信無効）は成果物の生成完了をもって確定
#===== ▲修正15 ここまで =====
