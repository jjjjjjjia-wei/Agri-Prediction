// src/App.jsx
import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// 全域常數
const API_BASE_URL = 'http://127.0.0.1:8000';
const DAYS_BACK_FOR_ALERT = 14;
const WEEK_HIGH_DAYS = 7;
const COLORS = ['#3498db', '#e74c3c', '#2ecc71', '#f1c40f', '#9b59b6', '#e67e22', '#1abc9c', '#34495e'];

function App() {
  const [activeTab, setActiveTab] = useState('query');
  const [markets, setMarkets] = useState([]);
  const [marketMap, setMarketMap] = useState({});
  const [dateMode, setDateMode] = useState('single'); 
  const [selectedMarkets, setSelectedMarkets] = useState(['104']);
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  
  const [queryData, setQueryData] = useState(null);
  const [predictData, setPredictData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE_URL}/markets`)
      .then(res => res.json())
      .then(data => {
        setMarkets(data.markets);
        const map = {};
        data.markets.forEach(m => map[m.code] = m.name);
        setMarketMap(map);
      })
      .catch(() => {
        setError('無法載入市場列表，請檢查網路連線');
      });
  }, []);

  const handleMarketChange = (code) => {
    if (activeTab === 'predict' || activeTab === 'alert') {
      setSelectedMarkets([code]);
    } else {
      setSelectedMarkets(prev => 
        prev.includes(code) 
          ? prev.filter(x => x !== code)
          : [...prev, code]
      );
    }
  };

  const handleSearch = async () => {
    if (selectedMarkets.length === 0) {
      setError('請至少選擇一個市場！');
      return;
    }
    
    setLoading(true);
    setQueryData(null);
    setPredictData(null);
    setError(null);

    const mCodes = selectedMarkets.join(',');
    const targetDate = (activeTab === 'predict' || activeTab === 'alert') 
      ? new Date().toISOString().split('T')[0] 
      : selectedDate;

    try {
      if (activeTab === 'predict') {
        const res = await fetch(`${API_BASE_URL}/predict?market_code=${selectedMarkets[0]}`);
        if (res.ok) {
          setPredictData(await res.json());
        } else {
          setError('預測失敗，請檢查後端服務與模型檔案');
        }
      } else {
        const daysBack = (activeTab === 'alert' || dateMode === 'range') ? DAYS_BACK_FOR_ALERT : 0;
        const startDate = new Date(new Date(targetDate).setDate(new Date(targetDate).getDate() - daysBack))
                          .toISOString().split('T')[0];
        
        const res = await fetch(`${API_BASE_URL}/history_price?market_code=${mCodes}&start_date=${startDate}&end_date=${targetDate}`);
        if (res.ok) {
          const result = await res.json();
          setQueryData({
            is_rest_day: result.is_rest_day,
            list: result.歷史數據 || []
          });
          
          if (!result.is_rest_day && (!result.歷史數據 || result.歷史數據.length === 0)) {
            setError('所選日期與市場查無資料！');
          }
        } else {
          setError('查詢失敗，請稍後再試');
        }
      }
    } catch (error) {
      setError('連線失敗！請確認後端 API 是否啟動');
    } finally {
      setLoading(false);
    }
  };

  const getTrendData = () => {
    if (!queryData || !queryData.list) return [];
    const dates = [...new Set(queryData.list.map(d => d.TransDate))];
    return dates.map(date => {
      const row = { TransDate: date };
      queryData.list.filter(d => d.TransDate === date).forEach(d => {
        if (d.MarketCode) {
          row[d.MarketCode] = d.Avg_Price;
        }
      });
      return row;
    });
  };

  const checkWeeklyHigh = useMemo(() => {
    if (!queryData || !queryData.list || activeTab !== 'alert' || queryData.list.length === 0) return null;
    const sorted = [...queryData.list].sort((a, b) => new Date(b.TransDate) - new Date(a.TransDate));
    const latest = sorted[0];
    const past7Days = sorted.slice(1, WEEK_HIGH_DAYS + 1);
    const maxPast = past7Days.length > 0 ? Math.max(...past7Days.map(d => d.Avg_Price)) : 0;
    return { isHighest: latest.Avg_Price >= maxPast, latest, maxPast };
  }, [queryData, activeTab]);

  return (
    <div style={{ padding: '20px', maxWidth: '1050px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h1 style={{ textAlign: 'center', color: '#f0f2f4' }}>甘藍菜價全方位決策系統</h1>

      {error && (
        <div style={{ background: '#e74c3c', color: 'white', padding: '12px', borderRadius: '8px', marginBottom: '20px', textAlign: 'center' }}>
          {error}
        </div>
      )}

      {/* 頂部頁籤選單 */}
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '25px' }}>
        <button onClick={() => { setActiveTab('query'); setError(null); }} style={btnStyle(activeTab === 'query')}>價格查詢</button>
        <button onClick={() => { setActiveTab('predict'); setSelectedMarkets([selectedMarkets[0] || '104']); setError(null); }} style={btnStyle(activeTab === 'predict')}>AI 預測</button>
        <button onClick={() => { setActiveTab('alert'); setSelectedMarkets([selectedMarkets[0] || '104']); setError(null); }} style={btnStyle(activeTab === 'alert', true)}>警示系統</button>
      </div>

      {/* 條件篩選面板 */}
      <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '12px', marginBottom: '25px' }}>
        <div style={{ marginBottom: '15px', display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          
          {activeTab === 'query' && (
            <>
              <select value={dateMode} onChange={(e) => setDateMode(e.target.value)} style={inputStyle}>
                <option value="single">單日快照</option>
                <option value="range">14天趨勢</option>
              </select>
              <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} style={inputStyle} />
            </>
          )}

          <button 
            onClick={handleSearch} 
            disabled={loading}
            style={{ 
              ...inputStyle, 
              background: loading ? '#95a5a6' : '#27ae60', 
              color: 'white', 
              border: 'none', 
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {loading ? 'AI 推算中...' : '開始執行'}
          </button>
        </div>
        
        {/* 市場選擇區 */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
          {markets.map(m => (
            <label key={m.code} style={{ fontSize: '14px', cursor: 'pointer', padding: '6px 12px', background: selectedMarkets.includes(m.code) ? '#3498db' : '#fff', color: selectedMarkets.includes(m.code) ? 'white' : 'black', borderRadius: '6px', border: '1px solid #3498db' }}>
              <input 
                type={(activeTab === 'predict' || activeTab === 'alert') ? 'radio' : 'checkbox'} 
                checked={selectedMarkets.includes(m.code)} 
                onChange={() => handleMarketChange(m.code)}
                style={{ marginRight: '5px' }}
              />
              {m.name}
            </label>
          ))}
        </div>
      </div>

      {/* 結果顯示區塊 */}
      <div style={{ minHeight: '400px' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
            AI 模型推算中，請稍候...
          </div>
        )}

        {/* 1. 價格查詢頁籤 */}
        {!loading && activeTab === 'query' && queryData && (
          <div>
            {dateMode === 'single' ? (
              queryData.is_rest_day ? (
                <div style={{ ...cardStyle, textAlign: 'center', padding: '50px', backgroundColor: '#fff3cd', border: '1px solid #ffeeba' }}>
                  <h2 style={{ color: '#856404' }}>選擇日期為市場休息日</h2>
                  <p style={{ color: '#856404', fontSize: '14px', marginTop: '10px' }}>當天無批發交易數據</p>
                </div>
              ) : selectedMarkets.length === 1 ? (
                queryData.list.length > 0 ? (
                  <div style={cardStyle}>
                    <h2>{marketMap[queryData.list[0].MarketCode]} - {queryData.list[0].TransDate}</h2>
                    <h1 style={{ color: '#27ae60' }}>均價：{queryData.list[0].Avg_Price} 元/kg</h1>
                    <h2 style={{ color: '#34495e' }}>交易量：{queryData.list[0].Trans_Quantity?.toLocaleString()} kg</h2>
                  </div>
                ) : (
                  <div style={{ ...cardStyle, textAlign: 'center', color: '#95a5a6' }}>查無當日交易資料</div>
                )
              ) : (
                <div style={{ display: 'flex', gap: '20px', height: '350px', flexWrap: 'wrap' }}>
                  <div style={{ ...cardStyle, flex: 1, minWidth: '300px' }}>
                    <h4 style={{ textAlign: 'center' }}>各市場價格比較</h4>
                    <ResponsiveContainer width="100%" height="85%">
                      <BarChart data={queryData.list}>
                        <XAxis dataKey="MarketCode" tickFormatter={v => marketMap[v]} />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="Avg_Price" fill="#3498db" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{ ...cardStyle, flex: 1, minWidth: '300px' }}>
                    <h4 style={{ textAlign: 'center' }}>交易量佔比</h4>
                    <ResponsiveContainer width="100%" height="85%">
                      <PieChart>
                        <Pie data={queryData.list} dataKey="Trans_Quantity" nameKey="MarketCode" outerRadius={80} label={({ payload }) => marketMap[payload.MarketCode]}>
                          {queryData.list.map((entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )
            ) : (
              <div style={{ ...cardStyle, height: '400px' }}>
                <h4 style={{ textAlign: 'center' }}>14天價格走勢</h4>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={getTrendData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="TransDate" />
                    <YAxis domain={['auto', 'auto']} />
                    <Tooltip />
                    <Legend />
                    {selectedMarkets.map((m, i) => <Line key={m} type="monotone" dataKey={m} name={marketMap[m] || m} stroke={COLORS[i % COLORS.length]} strokeWidth={3} />)}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {/* 2. AI 預測頁籤內容 (含歷史+未來平滑曲線圖與三階段預測) */}
        {!loading && activeTab === 'predict' && predictData && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* 頂部三階段預測卡片 */}
            <div style={{ ...cardStyle, textAlign: 'center' }}>
              <h2 style={{ color: '#2c3e50', margin: '0 0 5px 0' }}>預測市場：{predictData.市場名稱}</h2>
              <p style={{ color: '#7f8c8d', fontSize: '13px', margin: 0 }}>特徵基準日：{predictData.特徵資料日期}</p>

              <div style={{ display: 'flex', justifyContent: 'space-around', gap: '20px', marginTop: '25px', flexWrap: 'wrap' }}>
                
                {/* 1. 明日預測 */}
                <div style={{ flex: 1, minWidth: '180px', padding: '15px', background: '#f8f9fa', borderRadius: '10px' }}>
                  <p style={{ fontWeight: 'bold', color: '#34495e', margin: '0 0 10px 0' }}>預測明天價格 (t+1)</p>
                  <h1 style={{ color: '#e74c3c', fontSize: '32px', margin: '5px 0' }}>
                    {predictData.預測明天價格} <span style={{ fontSize: '16px' }}>元/kg</span>
                  </h1>
                  {predictData.預測明天提醒 === '週最高價' && (
                    <span style={{ background: '#fce4e4', color: '#e74c3c', padding: '3px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>
                      🚨 週最高價提醒
                    </span>
                  )}
                  {predictData.預測明天提醒 === '週最低價' && (
                    <span style={{ background: '#e8f8f5', color: '#27ae60', padding: '3px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>
                      📉 週最低價 (相對便宜)
                    </span>
                  )}
                </div>

                {/* 2. 三天後預測 (黃金採購點) */}
                <div style={{ flex: 1, minWidth: '180px', padding: '15px', background: '#eaf2f8', borderRadius: '10px', border: '1px solid #aed6f1' }}>
                  <p style={{ fontWeight: 'bold', color: '#1b4f72', margin: '0 0 10px 0' }}>🎯 三天後價格 (t+3)</p>
                  <h1 style={{ color: '#2980b9', fontSize: '32px', margin: '5px 0' }}>
                    {predictData.預測三天後價格} <span style={{ fontSize: '16px' }}>元/kg</span>
                  </h1>
                  <span style={{ background: '#d4efdf', color: '#196f3d', padding: '3px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>
                    最佳採購決策點
                  </span>
                </div>

                {/* 3. 下週預測 */}
                <div style={{ flex: 1, minWidth: '180px', padding: '15px', background: '#f8f9fa', borderRadius: '10px' }}>
                  <p style={{ fontWeight: 'bold', color: '#34495e', margin: '0 0 10px 0' }}>預測下週價格 (t+7)</p>
                  <h1 style={{ color: '#e67e22', fontSize: '32px', margin: '5px 0' }}>
                    {predictData.預測下週價格} <span style={{ fontSize: '16px' }}>元/kg</span>
                  </h1>
                  {predictData.預測下週提醒 === '週最高價' && (
                    <span style={{ background: '#fce4e4', color: '#e74c3c', padding: '3px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>
                      🚨 週最高價提醒
                    </span>
                  )}
                  {predictData.預測下週提醒 === '週最低價' && (
                    <span style={{ background: '#e8f8f5', color: '#27ae60', padding: '3px 8px', borderRadius: '10px', fontSize: '12px', fontWeight: 'bold' }}>
                      📉 週最低價 (相對便宜)
                    </span>
                  )}
                </div>

              </div>
            </div>

            {/* 底部：歷史真實價 + 未來預測平滑曲線圖 */}
            <div style={{ ...cardStyle, height: '420px' }}>
              <h3 style={{ textAlign: 'center', color: '#2c3e50', marginBottom: '15px' }}>
                📈 {predictData.市場名稱} - 歷史真實均價與 AI 預測趨勢曲線
              </h3>
              <ResponsiveContainer width="100%" height="85%">
                <LineChart data={predictData.趨勢圖資料} margin={{ top: 10, right: 30, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis domain={['auto', 'auto']} unit="元" />
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value} 元/kg`, 
                      name === 'actual_price' ? '歷史真實均價' : 'AI 預測價格'
                    ]}
                  />
                  <Legend />
                  
                  {/* 1. 過去 5 天真實歷史價格 (藍色實線) */}
                  <Line 
                    type="monotone" 
                    dataKey="actual_price" 
                    name="歷史真實均價" 
                    stroke="#3498db" 
                    strokeWidth={3} 
                    dot={{ r: 5, fill: '#3498db' }}
                    activeDot={{ r: 8 }}
                    connectNulls
                  />

                  {/* 2. 未來 3 階段 AI 預測價格 (橘紅色虛線) */}
                  <Line 
                    type="monotone" 
                    dataKey="predict_price" 
                    name="AI 預測價格" 
                    stroke="#e67e22" 
                    strokeWidth={3} 
                    strokeDasharray="5 5" 
                    dot={{ r: 6, fill: '#e67e22' }}
                    activeDot={{ r: 8 }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

          </div>
        )}

        {/* 3. 警示系統頁籤 */}
        {!loading && activeTab === 'alert' && queryData && checkWeeklyHigh && (
          <div style={{ ...cardStyle, textAlign: 'center', padding: '60px' }}>
            <h1 style={{ color: checkWeeklyHigh.isHighest ? '#e74c3c' : '#27ae60' }}>
              {checkWeeklyHigh.isHighest ? '🚨 警報：當前為週最高價！' : '✅ 價格穩定'}
            </h1>
            <p style={{ fontSize: '20px' }}>{marketMap[checkWeeklyHigh.latest.MarketCode]} 當前價格：{checkWeeklyHigh.latest.Avg_Price} 元</p>
            <p>過去 7 天最高：{checkWeeklyHigh.maxPast} 元</p>
          </div>
        )}

        {/* 預設提示 */}
        {!loading && !queryData && !predictData && (
          <div style={{ ...cardStyle, textAlign: 'center', padding: '60px', color: '#95a5a6' }}>
            <p style={{ fontSize: '18px' }}>請選擇市場並點擊「開始執行」進行查詢</p>
          </div>
        )}
      </div>
    </div>
  );
}

const btnStyle = (act, isAlert) => ({ 
  padding: '10px 20px', 
  cursor: 'pointer', 
  background: act ? (isAlert ? '#e74c3c' : '#3498db') : '#ddd', 
  color: act ? 'white' : 'black', 
  border: 'none', 
  borderRadius: '8px', 
  fontWeight: 'bold',
  transition: 'all 0.3s'
});

const inputStyle = { 
  padding: '8px', 
  borderRadius: '6px', 
  border: '1px solid #ccc',
  fontSize: '14px'
};

const cardStyle = { 
  background: 'white', 
  padding: '25px', 
  borderRadius: '12px', 
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)', 
  boxSizing: 'border-box' 
};

export default App;