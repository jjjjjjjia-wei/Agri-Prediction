import { useState, useEffect, useMemo } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Constants
const API_BASE_URL = 'http://127.0.0.1:8000';
const DAYS_BACK_FOR_ALERT = 14;
const DAYS_BACK_FOR_TREND = 14;
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
    const endDate = selectedDate;

    try {
      if (activeTab === 'predict') {
        const res = await fetch(`${API_BASE_URL}/predict?market_code=${selectedMarkets[0]}`);
        if (res.ok) {
          setPredictData(await res.json());
        } else {
          setError('預測失敗，請檢查後端');
        }
      } else {
        const daysBack = (activeTab === 'alert' || dateMode === 'range') ? DAYS_BACK_FOR_ALERT : 0;
        const startDate = new Date(new Date(selectedDate).setDate(new Date(selectedDate).getDate() - daysBack))
                          .toISOString().split('T')[0];
        
        const res = await fetch(`${API_BASE_URL}/history_price?market_code=${mCodes}&start_date=${startDate}&end_date=${endDate}`);
        if (res.ok) {
          const result = await res.json();
          if (result.歷史數據 && result.歷史數據.length > 0) {
            setQueryData(result.歷史數據);
          } else {
            setError('所選日期與市場查無資料！');
          }
        } else {
          setError('查詢失敗，請稍後再試');
        }
      }
    } catch (error) {
      setError('連線失敗！請確認後端服務是否啟動');
    } finally {
      setLoading(false);
    }
  };

  const getTrendData = () => {
    if (!queryData) return [];
    const dates = [...new Set(queryData.map(d => d.TransDate))];
    return dates.map(date => {
      const row = { TransDate: date };
      queryData.filter(d => d.TransDate === date).forEach(d => {
        if (d.MarketCode) {
          row[d.MarketCode] = d.Avg_Price;
        }
      });
      return row;
    });
  };

  const checkWeeklyHigh = useMemo(() => {
    if (!queryData || activeTab !== 'alert' || queryData.length === 0) return null;
    const sorted = [...queryData].sort((a, b) => new Date(b.TransDate) - new Date(a.TransDate));
    const latest = sorted[0];
    const past7Days = sorted.slice(1, WEEK_HIGH_DAYS + 1);
    const maxPast = past7Days.length > 0 ? Math.max(...past7Days.map(d => d.Avg_Price)) : 0;
    return { isHighest: latest.Avg_Price >= maxPast, latest, maxPast };
  }, [queryData, activeTab]);

  const alertInfo = checkWeeklyHigh;

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'sans-serif' }}>
      <h1 style={{ textAlign: 'center', color: '#2c3e50' }}>🥦 菜價全方位決策系統</h1>

      {error && (
        <div style={{ 
          background: '#e74c3c', 
          color: 'white', 
          padding: '12px', 
          borderRadius: '8px', 
          marginBottom: '20px',
          textAlign: 'center'
        }}>
          {error}
        </div>
      )}

      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center', marginBottom: '25px' }}>
        <button onClick={() => setActiveTab('query')} style={btnStyle(activeTab === 'query')}>價格查詢</button>
        <button onClick={() => { setActiveTab('predict'); setSelectedMarkets([selectedMarkets[0] || '104']); setError(null); }} style={btnStyle(activeTab === 'predict')}>AI 預測</button>
        <button onClick={() => { setActiveTab('alert'); setSelectedMarkets([selectedMarkets[0] || '104']); setError(null); }} style={btnStyle(activeTab === 'alert', true)}>警示系統</button>
      </div>

      <div style={{ background: '#f8f9fa', padding: '20px', borderRadius: '12px', marginBottom: '25px' }}>
        <div style={{ marginBottom: '15px', display: 'flex', gap: '10px', flexWrap: 'wrap', alignItems: 'center' }}>
          {activeTab === 'query' && (
            <select value={dateMode} onChange={(e) => setDateMode(e.target.value)} style={inputStyle}>
              <option value="single">單日快照</option>
              <option value="range">14天趨勢</option>
            </select>
          )}
          <input type="date" value={selectedDate} onChange={(e) => setSelectedDate(e.target.value)} style={inputStyle} />
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
            {loading ? '計算中...' : '開始執行'}
          </button>
        </div>
        
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

      <div style={{ minHeight: '400px' }}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px', color: '#7f8c8d' }}>
            載入中，請稍候...
          </div>
        )}

        {!loading && activeTab === 'query' && queryData && (
          <div>
            {dateMode === 'single' ? (
              selectedMarkets.length === 1 ? (
                <div style={cardStyle}>
                  <h2>{marketMap[queryData[0].MarketCode]} - {queryData[0].TransDate}</h2>
                  <h1 style={{color: '#27ae60'}}>均價：{queryData[0].Avg_Price} 元/kg</h1>
                  <h2 style={{color: '#34495e'}}>交易量：{queryData[0].Trans_Quantity?.toLocaleString()} kg</h2>
                </div>
              ) : (
                <div style={{ display: 'flex', gap: '20px', height: '350px', flexWrap: 'wrap' }}>
                  <div style={{...cardStyle, flex: 1, minWidth: '300px'}}>
                    <h4 style={{textAlign: 'center'}}>各市場價格比較</h4>
                    <ResponsiveContainer width="100%" height="85%">
                      <BarChart data={queryData}>
                        <XAxis dataKey="MarketCode" tickFormatter={v=>marketMap[v]}/>
                        <YAxis/>
                        <Tooltip/>
                        <Bar dataKey="Avg_Price" fill="#3498db" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                  <div style={{...cardStyle, flex: 1, minWidth: '300px'}}>
                    <h4 style={{textAlign: 'center'}}>交易量佔比</h4>
                    <ResponsiveContainer width="100%" height="85%">
                      <PieChart>
                        <Pie data={queryData} dataKey="Trans_Quantity" nameKey="MarketCode" outerRadius={80} label={({payload})=>marketMap[payload.MarketCode]}>
                          {queryData.map((entry, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                        </Pie>
                        <Tooltip/>
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )
            ) : (
              <div style={{...cardStyle, height: '400px'}}>
                <h4 style={{textAlign: 'center'}}>14天價格走勢</h4>
                <ResponsiveContainer width="100%" height="85%">
                  <LineChart data={getTrendData()}>
                    <CartesianGrid strokeDasharray="3 3"/>
                    <XAxis dataKey="TransDate"/>
                    <YAxis domain={['auto', 'auto']}/>
                    <Tooltip/>
                    <Legend/>
                    {selectedMarkets.map((m, i) => <Line key={m} type="monotone" dataKey={m} name={marketMap[m] || m} stroke={COLORS[i % COLORS.length]} strokeWidth={3} />)}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        )}

        {!loading && activeTab === 'predict' && predictData && (
          <div style={{...cardStyle, textAlign: 'center', padding: '60px'}}>
            <h2>🔮 AI 預測：{predictData.市場名稱}</h2>
            <div style={{display: 'flex', justifyContent: 'center', gap: '40px', marginTop: '30px', flexWrap: 'wrap'}}>
              <div><p>預測明天</p><h1 style={{color: '#e74c3c'}}>{predictData.預測明天價格} 元</h1></div>
              <div style={{borderLeft: '1px solid #ddd', paddingLeft: '40px'}}><p>預測下週</p><h1 style={{color: '#e67e22'}}>{predictData.預測下週價格} 元</h1></div>
            </div>
          </div>
        )}

        {!loading && activeTab === 'alert' && queryData && alertInfo && (
          <div style={{...cardStyle, textAlign: 'center', padding: '60px'}}>
            <h1 style={{color: alertInfo.isHighest ? '#e74c3c' : '#27ae60'}}>
              {alertInfo.isHighest ? '🚨 警報：當前為週最高價！' : '✅ 價格穩定'}
            </h1>
            <p style={{fontSize: '20px'}}>{marketMap[alertInfo.latest.MarketCode]} 當前價格：{alertInfo.latest.Avg_Price} 元</p>
            <p>過去 7 天最高：{alertInfo.maxPast} 元</p>
          </div>
        )}

        {!loading && !queryData && !predictData && activeTab !== 'alert' && (
          <div style={{...cardStyle, textAlign: 'center', padding: '60px', color: '#95a5a6'}}>
            <p style={{fontSize: '18px'}}>請選擇市場和日期，然後點擊「開始執行」查詢資料</p>
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
  flex: 1, 
  boxSizing: 'border-box' 
};

export default App;