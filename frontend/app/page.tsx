'use client'

import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'

type StrategyPayload = {
  data: Record<string, string | number>[]
  stats: Record<string, string | number>[]
}

type AnalysisResponse = {
  analysis_name: string
  ticker: string
  price_data: Record<string, string | number>[]
  strategies: Record<string, StrategyPayload>
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'

const buildStrategies = (emaPeriods: string, rsiPeriods: string, macdSets: string) => {
  const strategies: string[] = []
  const parsedEma = emaPeriods.split(',').map((value) => value.trim()).filter(Boolean)
  const parsedRsi = rsiPeriods.split(',').map((value) => value.trim()).filter(Boolean)

  parsedEma.forEach((ema) => {
    parsedRsi.forEach((rsi) => {
      strategies.push(`EMA_${ema}-RSI_${rsi}`)
    })
  })

  macdSets
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)
    .forEach((setValue) => {
      const parts = setValue.split(' ').filter(Boolean)
      if (parts.length === 3) {
        strategies.push(`MACD_${parts[0]}_${parts[1]}_${parts[2]}`)
      }
    })

  return strategies
}

export default function Home() {
  const [analysisName, setAnalysisName] = useState('MyAnalysis')
  const [ticker, setTicker] = useState('AAPL')
  const [emaPeriods, setEmaPeriods] = useState('5,10')
  const [rsiPeriods, setRsiPeriods] = useState('14')
  const [macdSets, setMacdSets] = useState('12 26 9')
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null)
  const [error, setError] = useState('')

  const strategyNames = useMemo(() => buildStrategies(emaPeriods, rsiPeriods, macdSets), [emaPeriods, rsiPeriods, macdSets])

  const chartData = useMemo(() => {
    if (!analysis) {
      return []
    }

    const firstStrategy = Object.keys(analysis.strategies)[0]
    const strategyRows = firstStrategy ? analysis.strategies[firstStrategy].data : []
    const profitByDate = new Map<string, number>()

    strategyRows.forEach((row) => {
      const dateValue = String(row.Date)
      const profit = Number(row.total_profit ?? 0)
      profitByDate.set(dateValue, profit)
    })

    return analysis.price_data.slice(-250).map((row) => {
      const dateValue = String(row.Date)
      return {
        Date: dateValue,
        Close: Number(row.Close),
        StrategyProfit: profitByDate.get(dateValue) ?? null
      }
    })
  }, [analysis])

  const post = async (path: string, body: object) => {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    const payload = await response.json()
    if (!response.ok) {
      throw new Error(payload.detail || 'Request failed')
    }
    return payload
  }

  const createAnalysis = async () => {
    try {
      setError('')
      const payload = await post('/api/analysis/create', { analysis_name: analysisName, ticker })
      setAnalysis(payload)
    } catch (requestError) {
      setError((requestError as Error).message)
    }
  }

  const loadAnalysis = async () => {
    try {
      setError('')
      const payload = await post('/api/analysis/load', { analysis_name: analysisName })
      setAnalysis(payload)
    } catch (requestError) {
      setError((requestError as Error).message)
    }
  }

  const runStrategies = async () => {
    try {
      setError('')
      const payload = await post('/api/analysis/run', {
        analysis_name: analysisName,
        indicator_params: {
          ema: emaPeriods.split(',').map((value) => value.trim()).filter(Boolean),
          rsi: rsiPeriods.split(',').map((value) => value.trim()).filter(Boolean),
          macd: macdSets.split(',').map((value) => value.trim()).filter(Boolean)
        },
        strategy_names: strategyNames
      })
      setAnalysis(payload)
    } catch (requestError) {
      setError((requestError as Error).message)
    }
  }

  return (
    <main>
      <h1>Analytical Trading Dashboard (Next.js)</h1>

      <section>
        <div className="grid">
          <label>
            Analysis Name
            <input value={analysisName} onChange={(event) => setAnalysisName(event.target.value)} />
          </label>
          <label>
            Ticker
            <input value={ticker} onChange={(event) => setTicker(event.target.value.toUpperCase())} />
          </label>
        </div>
        <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
          <button onClick={createAnalysis}>Create</button>
          <button className="secondary" onClick={loadAnalysis}>Load</button>
          <button onClick={runStrategies}>Run Strategies</button>
        </div>
        {error && <p className="error">{error}</p>}
      </section>

      <section>
        <h2>Indicator parameters</h2>
        <div className="grid">
          <label>
            EMA periods
            <input value={emaPeriods} onChange={(event) => setEmaPeriods(event.target.value)} />
          </label>
          <label>
            RSI periods
            <input value={rsiPeriods} onChange={(event) => setRsiPeriods(event.target.value)} />
          </label>
          <label>
            MACD sets (fast slow signal)
            <input value={macdSets} onChange={(event) => setMacdSets(event.target.value)} />
          </label>
        </div>
        <p>Generated strategies: {strategyNames.join(', ') || 'None'}</p>
      </section>

      {analysis && (
        <>
          <section>
            <h2>{analysis.analysis_name} ({analysis.ticker})</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="Date" minTickGap={40} />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="Close" stroke="#7c3aed" dot={false} />
                <Line yAxisId="right" type="monotone" dataKey="StrategyProfit" stroke="#0f766e" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </section>

          {Object.entries(analysis.strategies).map(([name, payload]) => (
            <section key={name}>
              <h3>{name} stats</h3>
              <table>
                <thead>
                  <tr>
                    {payload.stats[0] && Object.keys(payload.stats[0]).map((header) => <th key={header}>{header}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {payload.stats.map((row, index) => (
                    <tr key={`${name}-${index}`}>
                      {Object.values(row).map((value, rowIndex) => <td key={`${name}-${index}-${rowIndex}`}>{String(value)}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          ))}
        </>
      )}
    </main>
  )
}
