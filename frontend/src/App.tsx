import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { ImportFiles } from './pages/ImportFiles';
import { SalesAnalysis } from './pages/SalesAnalysis';
import { SalesDetails } from './pages/SalesDetails';
import { CaratBinAnalysis } from './pages/CaratBinAnalysis';
import { ShapeAnalysis } from './pages/ShapeAnalysis';
import { ColorAnalysis } from './pages/ColorAnalysis';
import { ClarityAnalysis } from './pages/ClarityAnalysis';
import { AIPricingIntelligence } from './pages/AIPricingIntelligence';
import { CaratMatrixPage } from './pages/CaratMatrixPage';
import { InventoryIntelligence } from './pages/InventoryIntelligence';

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/import" element={<ImportFiles />} />
        <Route path="/sales-analysis" element={<SalesAnalysis />} />
        <Route path="/sales-details" element={<SalesDetails />} />
        <Route path="/carat-analysis" element={<CaratBinAnalysis />} />
        <Route path="/shape-analysis" element={<ShapeAnalysis />} />
        <Route path="/color-analysis" element={<ColorAnalysis />} />
        <Route path="/clarity-analysis" element={<ClarityAnalysis />} />
        <Route path="/ai-pricing" element={<AIPricingIntelligence />} />
        <Route path="/carat-matrix" element={<CaratMatrixPage />} />
        <Route path="/inventory-intelligence" element={<InventoryIntelligence />} />
      </Routes>
    </Layout>
  );
}

export default App;
