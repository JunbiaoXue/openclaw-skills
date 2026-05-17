"""
双色球预测 - 最新数据版 (2003-2025, 3296期)
"""
import numpy as np
from collections import Counter
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import csv, json

# ========== 数据加载 ==========
data = []
with open('/home/xjb/work/lottery_prediction/ssq_all.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            red = [int(x) for x in [row['红球1'], row['红球2'], row['红球3'], row['红球4'], row['红球5'], row['红球6']]]
            blue = int(row['蓝球'])
            data.append({'red': red, 'blue': blue})
        except:
            continue

print(f"总数据: {len(data)} 期")
print(f"最新: {data[0]['red']} + {data[0]['blue']:02d}")

# ========== 特征工程 ==========
def build_features(data, idx, windows=[5, 10, 20, 50]):
    features = []
    history = data[idx+1:]
    if len(history) < max(windows):
        return None, None
    
    # 多窗口频率
    for w in windows:
        freq = np.zeros(33)
        for item in history[:w]:
            for r in item['red']: freq[r-1] += 1
        freq /= w
        features.extend(freq.tolist())
    
    # 遗漏
    miss = np.zeros(33)
    for n in range(1, 34):
        for i, item in enumerate(history):
            if n in item['red']: miss[n-1] = i; break
        else: miss[n-1] = min(len(history), 200)
    features.extend((miss / 200).tolist())
    
    # 趋势
    freq5 = np.zeros(33)
    freq20 = np.zeros(33)
    for item in history[:5]:
        for r in item['red']: freq5[r-1] += 1
    for item in history[:20]:
        for r in item['red']: freq20[r-1] += 1
    freq5 /= 5; freq20 /= 20
    features.extend((freq5 - freq20).tolist())
    
    # 统计特征
    r20 = history[:20]
    features.append(np.mean([sum(1 for r in x['red'] if r%2==1) for x in r20]) / 6)
    features.append(np.mean([sum(1 for r in x['red'] if r>16) for x in r20]) / 6)
    sums = [sum(x['red']) for x in r20]
    features.append(np.mean(sums) / 150)
    features.append(np.std(sums) / 50)
    spans = [max(x['red']) - min(x['red']) for x in r20]
    features.append(np.mean(spans) / 33)
    if len(history) >= 2:
        features.append(len(set(history[0]['red']) & set(history[1]['red'])) / 6)
    else:
        features.append(0)
    consec = []
    for x in r20:
        s = sorted(x['red'])
        c = sum(1 for i in range(5) if s[i+1] == s[i]+1)
        consec.append(c)
    features.append(np.mean(consec) / 5)
    
    # 蓝球特征
    bf = np.zeros(16)
    for x in history[:50]: bf[x['blue']-1] += 1
    bf /= 50
    features.extend(bf.tolist())
    
    bm = np.zeros(16)
    for n in range(1, 17):
        for i, x in enumerate(history):
            if x['blue'] == n: bm[n-1] = i; break
        else: bm[n-1] = min(len(history), 100)
    features.extend((bm / 100).tolist())
    
    # 时序序列
    seq = np.zeros((10, 33))
    for k in range(min(10, len(history))):
        for r in history[k]['red']:
            seq[k][r-1] = 1
    
    return np.array(features, dtype=np.float32), seq.astype(np.float32)

# 构建数据
print("构建特征...")
X_feat_list, X_seq_list, y_red_list, y_blue_list = [], [], [], []
for idx in range(len(data)):
    feat, seq = build_features(data, idx)
    if feat is not None:
        X_feat_list.append(feat)
        X_seq_list.append(seq)
        rl = np.zeros(33)
        for r in data[idx]['red']: rl[r-1] = 1
        y_red_list.append(rl)
        y_blue_list.append(data[idx]['blue'] - 1)

X_feat = np.array(X_feat_list)
X_seq = np.array(X_seq_list)
y_red = np.array(y_red_list)
y_blue = np.array(y_blue_list)

# 训练集=早期85%, 测试集=近期15%
split = int(len(X_feat) * 0.85)
X_feat_train, X_feat_test = torch.FloatTensor(X_feat[:split]), torch.FloatTensor(X_feat[split:])
X_seq_train, X_seq_test = torch.FloatTensor(X_seq[:split]), torch.FloatTensor(X_seq[split:])
y_red_train, y_red_test = torch.FloatTensor(y_red[:split]), torch.FloatTensor(y_red[split:])
y_blue_train, y_blue_test = torch.LongTensor(y_blue[:split]), torch.LongTensor(y_blue[split:])

FEAT_DIM = X_feat_train.shape[1]
SEQ_LEN = X_seq_train.shape[1]
SEQ_DIM = X_seq_train.shape[2]
print(f"特征: {FEAT_DIM}, 序列: {SEQ_LEN}x{SEQ_DIM}")
print(f"训练集: {split}, 测试集: {len(X_feat)-split}")

# ========== Transformer 模型 ==========
class TransformerLottery(nn.Module):
    def __init__(self, feat_dim, seq_len, seq_dim, d_model=64, nhead=4, nlayers=2):
        super().__init__()
        self.seq_proj = nn.Linear(seq_dim, d_model)
        self.pos_enc = nn.Parameter(torch.randn(1, seq_len, d_model) * 0.02)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=128,
            dropout=0.1, batch_first=True, activation='gelu'
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=nlayers)
        self.seq_pool = nn.AdaptiveAvgPool1d(1)
        
        self.feat_enc = nn.Sequential(
            nn.Linear(feat_dim, 256), nn.LayerNorm(256), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(), nn.Dropout(0.2),
        )
        
        self.fusion = nn.Sequential(
            nn.Linear(128 + d_model, 128), nn.LayerNorm(128), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(128, 64), nn.GELU(),
        )
        self.red_head = nn.Sequential(nn.Linear(64, 33), nn.Sigmoid())
        self.blue_head = nn.Linear(64, 16)
    
    def forward(self, feat, seq):
        s = self.seq_proj(seq) + self.pos_enc
        s = self.transformer(s)
        s = self.seq_pool(s.permute(0,2,1)).squeeze(-1)
        f = self.feat_enc(feat)
        x = self.fusion(torch.cat([f, s], dim=-1))
        return self.red_head(x), self.blue_head(x)

# ========== Deep MLP ==========
class DeepMLP(nn.Module):
    def __init__(self, feat_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(feat_dim, 768), nn.LayerNorm(768), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(768, 512), nn.LayerNorm(512), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(512, 256), nn.LayerNorm(256), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(256, 128), nn.LayerNorm(128), nn.GELU(), nn.Dropout(0.1),
        )
        self.red_head = nn.Sequential(nn.Linear(128, 64), nn.GELU(), nn.Linear(64, 33), nn.Sigmoid())
        self.blue_head = nn.Sequential(nn.Linear(128, 32), nn.GELU(), nn.Linear(32, 16))
    
    def forward(self, feat, seq=None):
        x = self.net(feat)
        return self.red_head(x), self.blue_head(x)

# ========== Loss ==========
class LotteryLoss(nn.Module):
    def forward(self, rp, bp, rt, bt):
        red_bce = nn.functional.binary_cross_entropy(rp, rt)
        pt = rp * rt + (1 - rp) * (1 - rt)
        focal = -((1 - pt) ** 2 * torch.log(pt + 1e-8)).mean()
        red_loss = 0.5 * red_bce + 0.5 * focal
        blue_loss = nn.functional.cross_entropy(bp, bt)
        count_loss = ((rp.sum(1) - 6) ** 2).mean() * 0.05
        top6 = torch.topk(rp, 6, dim=1).values
        rank_loss = -torch.log(top6 + 1e-8).mean() * 0.15
        return red_loss + blue_loss + count_loss + rank_loss, red_loss, blue_loss, count_loss

# ========== 训练 ==========
def train_model(model, model_type, name, epochs=150):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=30, T_mult=2)
    criterion = LotteryLoss()
    
    train_ds = TensorDataset(X_feat_train, X_seq_train, y_red_train, y_blue_train)
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    
    best_red = 0
    best_state = None
    
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for bx, sx, br, bb in train_loader:
            bx, sx, br, bb = bx.to(device), sx.to(device), br.to(device), bb.to(device)
            optimizer.zero_grad()
            if model_type == 'transformer':
                rp, bp = model(bx, sx)
            else:
                rp, bp = model(bx)
            loss, _, _, _ = criterion(rp, bp, br, bb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()
        scheduler.step()
        
        if (epoch+1) % 20 == 0:
            model.eval()
            with torch.no_grad():
                if model_type == 'transformer':
                    rp, bp = model(X_feat_test.to(device), X_seq_test.to(device))
                else:
                    rp, bp = model(X_feat_test.to(device))
                
                top6 = torch.topk(rp, 6, dim=1).indices.cpu().numpy()
                red_hits = []
                for i in range(len(y_red_test)):
                    pred_set = set(top6[i])
                    true_set = set(np.where(y_red_test[i].numpy() == 1)[0])
                    red_hits.append(len(pred_set & true_set))
                
                avg_hit = np.mean(red_hits)
                ge2 = sum(1 for h in red_hits if h >= 2) / len(red_hits)
                blue_acc = (bp.argmax(1).cpu() == y_blue_test).float().mean().item()
                
                marker = ""
                if avg_hit > best_red:
                    best_red = avg_hit
                    best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
                    marker = " ★"
                
                print(f"  [{name}] Epoch {epoch+1:3d}: Loss={total_loss/len(train_loader):.4f} | Red={avg_hit:.3f}/6 (≥2:{ge2:.1%}) Blue={blue_acc:.1%}{marker}")
    
    if best_state:
        model.load_state_dict(best_state)
    return model, best_red

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\n设备: {device}")
print(f"{'='*70}")

print("\n训练 Transformer...")
model1 = TransformerLottery(FEAT_DIM, SEQ_LEN, SEQ_DIM)
model1, best1 = train_model(model1, 'transformer', 'TF', epochs=150)

print("\n训练 Deep MLP...")
model2 = DeepMLP(FEAT_DIM)
model2, best2 = train_model(model2, 'mlp', 'MLP', epochs=150)

print(f"\n{'='*70}")
print(f"随机基准: {6*6/33:.4f}/6")
print(f"Transformer: {best1:.4f}/6")
print(f"Deep MLP: {best2:.4f}/6")

# ========== 集成预测 ==========
print(f"\n{'='*70}")
print("集成预测 (MC Dropout x 1000)")

feat_latest, seq_latest = build_features(data, 0)
feat_t = torch.FloatTensor(feat_latest).unsqueeze(0)
seq_t = torch.FloatTensor(seq_latest).unsqueeze(0)

mc_red = Counter()
mc_blue = Counter()

for _ in range(1000):
    model1.train()
    model2.train()
    with torch.no_grad():
        rp1, bp1 = model1(feat_t.to(device), seq_t.to(device))
        rp2, bp2 = model2(feat_t.to(device))
    
    top6_1 = sorted((np.argsort(rp1[0].cpu().numpy())[-6:] + 1).tolist())
    top6_2 = sorted((np.argsort(rp2[0].cpu().numpy())[-6:] + 1).tolist())
    top_b1 = int(bp1[0].argmax().item()) + 1
    top_b2 = int(bp2[0].argmax().item()) + 1
    
    for r in top6_1: mc_red[r] += 1
    for r in top6_2: mc_red[r] += 1
    mc_blue[top_b1] += 1
    mc_blue[top_b2] += 1

final_red = sorted([n for n, _ in mc_red.most_common(6)])
final_blue = mc_blue.most_common(1)[0][0]

print(f"\n🎯 最终预测（下一期）:")
print(f"  🔴 红球: {final_red}")
print(f"  🔵 蓝球: {final_blue:02d}")

print(f"\n红球投票 Top 12:")
for n, c in mc_red.most_common(12):
    pct = c / 2000 * 100
    bar = "█" * int(pct / 2)
    print(f"  {n:2d}: {bar} {pct:.1f}%")

print(f"\n蓝球投票 Top 5:")
for n, c in mc_blue.most_common(5):
    pct = c / 2000 * 100
    bar = "█" * int(pct / 2)
    print(f"  {n:2d}: {bar} {pct:.1f}%")

# 保存
torch.save({
    'transformer': model1.state_dict(),
    'deep_mlp': model2.state_dict(),
    'feat_dim': FEAT_DIM,
    'seq_len': SEQ_LEN,
    'seq_dim': SEQ_DIM,
    'best_red_transformer': best1,
    'best_red_mlp': best2,
}, '/home/xjb/work/lottery_prediction/model_final.pth')
print(f"\n✅ 模型已保存到 model_final.pth")
