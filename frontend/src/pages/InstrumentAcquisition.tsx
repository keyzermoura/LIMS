import React, { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  FileCheck2,
  FileCode,
  FileSpreadsheet,
  FileText,
  Filter,
  HardDrive,
  Hash,
  Link as LinkIcon,
  RefreshCw,
  Scale,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import { equipmentApi, instrumentDataApi } from "../lib/api";
import {
  InstrumentDataImport,
  InstrumentDataSummary,
  InstrumentFileFormat,
  LaboratoryEquipment,
} from "../lib/types";

export default function InstrumentAcquisition() {
  const [summary, setSummary] = useState<InstrumentDataSummary | null>(null);
  const [imports, setImports] = useState<InstrumentDataImport[]>([]);
  const [equipments, setEquipments] = useState<LaboratoryEquipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State
  const [selectedEquipmentId, setSelectedEquipmentId] = useState("");
  const [selectedFormat, setSelectedFormat] = useState<InstrumentFileFormat>("BALANCA_ASCII");
  const [rawText, setRawText] = useState("");
  const [fileName, setFileName] = useState("pesagem_balanca.txt");
  const [targetExecutionId, setTargetExecutionId] = useState("");

  // Inspect Modal
  const [inspectingItem, setInspectingItem] = useState<InstrumentDataImport | null>(null);
  // Map Modal
  const [mappingItem, setMappingItem] = useState<InstrumentDataImport | null>(null);
  const [mapExecutionId, setMapExecutionId] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sumRes, impRes, eqRes] = await Promise.all([
        instrumentDataApi.getSummary().catch(() => ({ total_imports: 0, mapped_imports: 0, unmapped_imports: 0 })),
        instrumentDataApi.list({ limit: 50 }),
        equipmentApi.list(),
      ]);
      setSummary(sumRes);
      setImports(impRes);
      setEquipments(eqRes);

      if (eqRes.length > 0 && !selectedEquipmentId) {
        setSelectedEquipmentId(eqRes[0].id);
      }
    } catch (err: any) {
      setError(err?.message || "Erro ao carregar dados de instrumentos.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUploadRaw = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEquipmentId || !rawText.trim()) {
      setError("Selecione um equipamento e forneça o conteúdo dos dados brutos.");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      setSuccessMsg(null);

      const created = await instrumentDataApi.uploadRaw({
        equipment_id: selectedEquipmentId,
        file_name: fileName || "instrument_data.raw",
        file_format: selectedFormat,
        raw_content: rawText,
        test_execution_id: targetExecutionId || undefined,
      });

      setSuccessMsg(`Dado bruto ingerido com sucesso! SHA-256: ${created.raw_file_hash_sha256.substring(0, 16)}...`);
      setRawText("");
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Falha na ingestão do dado analítico.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleMapExecution = async () => {
    if (!mappingItem || !mapExecutionId) return;

    try {
      setSubmitting(true);
      setError(null);
      await instrumentDataApi.mapToExecution(mappingItem.id, mapExecutionId);
      setSuccessMsg(`Dados do instrumento mapeados com sucesso na execução ${mapExecutionId}!`);
      setMappingItem(null);
      setMapExecutionId("");
      await loadData();
    } catch (err: any) {
      setError(err?.message || "Falha ao mapear leitura na execução de ensaio.");
    } finally {
      setSubmitting(false);
    }
  };

  const setSamplePreset = (format: InstrumentFileFormat) => {
    setSelectedFormat(format);
    if (format === "BALANCA_ASCII") {
      setFileName("balanca_mettler_lote01.txt");
      setRawText(
        "---- METTLER TOLEDO AT201 ----\n" +
        "Date: 16-Nov-2026\n" +
        "Tare:   +   2.1005 g\n" +
        "Gross:  +  14.5573 g\n" +
        "Net:    +  12.4568 g\n" +
        "Status: S (Stable)\n"
      );
    } else if (format === "UV_VIS_CSV") {
      setFileName("espectro_absorbancia.csv");
      setRawText(
        "Wavelength,Absorbance\n" +
        "220.0,0.045\n" +
        "240.0,0.180\n" +
        "260.0,1.854\n" +
        "280.0,0.312\n" +
        "300.0,0.065\n"
      );
    } else if (format === "CHROMATOGRAPHY_CSV") {
      setFileName("cromatograma_hplc_pureza.csv");
      setRawText(
        "Peak,RT,Area,Height,%Area\n" +
        "1,1.82,14200,1950,1.15\n" +
        "2,4.48,1218000,94200,98.85\n"
      );
    } else {
      setFileName("dados_brutos.json");
      setRawText(JSON.stringify({ device: "Sensor pH", ph: 7.02, temp: 24.8, stable: true }, null, 2));
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="h-7 w-7 text-indigo-600" />
            <h1 className="text-2xl font-bold tracking-tight text-slate-900">
              Aquisição Direta de Instrumentos Analíticos
            </h1>
          </div>
          <p className="text-sm text-slate-600 mt-1">
            Conectores de bancada, validação criptográfica SHA-256 e zero transcrição manual (ISO/IEC 17025 §7.11 & 21 CFR Part 11).
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-sm transition"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Atualizar Leituras
        </button>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-4 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm font-medium">{error}</div>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm font-medium">{successMsg}</div>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total de Ingestões</p>
            <p className="text-2xl font-bold text-slate-900 mt-1">{summary?.total_imports ?? 0}</p>
            <p className="text-xs text-slate-500 mt-1">Arquivos brutos auditados</p>
          </div>
          <div className="h-12 w-12 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <HardDrive className="h-6 w-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Mapeadas em Ensaios</p>
            <p className="text-2xl font-bold text-emerald-600 mt-1">{summary?.mapped_imports ?? 0}</p>
            <p className="text-xs text-emerald-600 font-medium mt-1">Zero Transcrição Manual</p>
          </div>
          <div className="h-12 w-12 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <FileCheck2 className="h-6 w-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Aguardando Vínculo</p>
            <p className="text-2xl font-bold text-amber-600 mt-1">{summary?.unmapped_imports ?? 0}</p>
            <p className="text-xs text-slate-500 mt-1">Leituras disponíveis</p>
          </div>
          <div className="h-12 w-12 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <Activity className="h-6 w-6" />
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Conformidade ALCOA+</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">100%</p>
            <p className="text-xs text-blue-600 font-medium mt-1">SHA-256 Imutável</p>
          </div>
          <div className="h-12 w-12 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
            <ShieldCheck className="h-6 w-6" />
          </div>
        </div>
      </div>

      {/* Ingestion Console & Preset Tabs */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b gap-3">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <UploadCloud className="h-5 w-5 text-indigo-600" />
              Terminal de Ingestão de Dados de Bancada
            </h2>
            <p className="text-sm text-slate-500">
              Cole o fluxo serial ou carregue os dados exportados pelo equipamento metrológico.
            </p>
          </div>

          {/* Quick presets */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold text-slate-500 uppercase">Modelos de Teste:</span>
            <button
              type="button"
              onClick={() => setSamplePreset("BALANCA_ASCII")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md border transition ${
                selectedFormat === "BALANCA_ASCII"
                  ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                  : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
              }`}
            >
              <Scale className="inline h-3.5 w-3.5 mr-1" />
              Balança RS-232
            </button>
            <button
              type="button"
              onClick={() => setSamplePreset("UV_VIS_CSV")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md border transition ${
                selectedFormat === "UV_VIS_CSV"
                  ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                  : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
              }`}
            >
              <FileSpreadsheet className="inline h-3.5 w-3.5 mr-1" />
              UV-Vis CSV
            </button>
            <button
              type="button"
              onClick={() => setSamplePreset("CHROMATOGRAPHY_CSV")}
              className={`px-2.5 py-1 text-xs font-medium rounded-md border transition ${
                selectedFormat === "CHROMATOGRAPHY_CSV"
                  ? "bg-indigo-50 border-indigo-300 text-indigo-700"
                  : "bg-slate-50 border-slate-200 text-slate-600 hover:bg-slate-100"
              }`}
            >
              <FileText className="inline h-3.5 w-3.5 mr-1" />
              HPLC Picos
            </button>
          </div>
        </div>

        <form onSubmit={handleUploadRaw} className="mt-5 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Equipamento Emissor (ISO 17025 §6.4) *
              </label>
              <select
                value={selectedEquipmentId}
                onChange={(e) => setSelectedEquipmentId(e.target.value)}
                required
                className="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Selecione o equipamento...</option>
                {equipments.map((eq) => (
                  <option key={eq.id} value={eq.id}>
                    {eq.code} - {eq.name} ({eq.calibration_status})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Formato do Protocolo / Arquivo *
              </label>
              <select
                value={selectedFormat}
                onChange={(e) => setSelectedFormat(e.target.value as InstrumentFileFormat)}
                required
                className="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="BALANCA_ASCII">Balança Analítica (RS-232 / ASCII)</option>
                <option value="UV_VIS_CSV">Espectrofotômetro UV-Vis (CSV / Varredura)</option>
                <option value="CHROMATOGRAPHY_CSV">Cromatógrafo HPLC/GC (Tabela de Picos)</option>
                <option value="GENERIC_JSON">Instrumento Digital (JSON Padronizado)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Nome do Arquivo de Evidência
              </label>
              <input
                type="text"
                value={fileName}
                onChange={(e) => setFileName(e.target.value)}
                placeholder="ex.: pesagem_01.txt"
                className="w-full text-sm rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Conteúdo dos Dados Brutos (Raw Stream) *
            </label>
            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              required
              placeholder="Cole os dados seriais brutos aqui..."
              className="w-full font-mono text-xs rounded-lg border border-slate-300 p-3 bg-slate-900 text-emerald-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="text-xs text-slate-500 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              O sistema calcula e audita o hash SHA-256 de forma imutável antes da gravação.
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow-md transition disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  Processando Leitura...
                </>
              ) : (
                <>
                  <UploadCloud className="h-4 w-4" />
                  Ingerir e Parsear Dados
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Acquisition Feed & Mapping Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-900">Histórico de Aquisições e Evidências Brutas</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Rastreabilidade metrológica completa para ensaios periciais e auditorias ISO/IEC 17025.
            </p>
          </div>
        </div>

        {imports.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <Cpu className="h-10 w-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm">Nenhum dado analítico importado até o momento.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b">
                <tr>
                  <th className="px-5 py-3">Data / Hora</th>
                  <th className="px-5 py-3">Arquivo & Formato</th>
                  <th className="px-5 py-3">Equipamento</th>
                  <th className="px-5 py-3">Hash SHA-256</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3 text-right">Ações</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {imports.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 transition">
                    <td className="px-5 py-3.5 text-xs text-slate-600 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString("pt-BR")}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900 flex items-center gap-1.5">
                        <FileCode className="h-4 w-4 text-indigo-500" />
                        {item.file_name}
                      </div>
                      <span className="text-xs text-slate-500 font-mono">{item.file_format}</span>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-700">
                      {equipments.find((e) => e.id === item.equipment_id)?.code || "Equipamento"}
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="flex items-center gap-1.5 font-mono text-xs text-slate-600 bg-slate-100 px-2 py-0.5 rounded max-w-fit">
                        <Hash className="h-3.5 w-3.5 text-slate-400" />
                        {item.raw_file_hash_sha256.substring(0, 12)}...
                      </div>
                    </td>
                    <td className="px-5 py-3.5">
                      {item.status === "MAPPED" ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3" />
                          Mapeado
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                          <Activity className="h-3 w-3" />
                          Importado
                        </span>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setInspectingItem(item)}
                          className="px-2.5 py-1 text-xs font-medium rounded border border-slate-200 text-slate-700 hover:bg-slate-100 transition"
                        >
                          Inspecionar
                        </button>
                        {item.status !== "MAPPED" && (
                          <button
                            onClick={() => {
                              setMappingItem(item);
                              setMapExecutionId("");
                            }}
                            className="px-2.5 py-1 text-xs font-semibold rounded bg-indigo-50 border border-indigo-200 text-indigo-700 hover:bg-indigo-100 transition flex items-center gap-1"
                          >
                            <LinkIcon className="h-3 w-3" />
                            Mapear
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Inspect Modal */}
      {inspectingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <FileCode className="h-5 w-5 text-indigo-600" />
                Dados Parseados e Integridade Criptográfica
              </h3>
              <button
                onClick={() => setInspectingItem(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>
            <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">
              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Hash SHA-256 Imutável:</span>
                <p className="font-mono text-xs text-slate-900 bg-slate-100 p-2 rounded mt-1 break-all">
                  {inspectingItem.raw_file_hash_sha256}
                </p>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Grandezas Parseadas:</span>
                <pre className="mt-1 p-3 bg-slate-900 text-emerald-400 font-mono text-xs rounded-lg overflow-x-auto">
                  {JSON.stringify(inspectingItem.parsed_data, null, 2)}
                </pre>
              </div>

              <div>
                <span className="text-xs font-semibold text-slate-500 uppercase">Dados Brutos Originais:</span>
                <pre className="mt-1 p-3 bg-slate-50 border border-slate-200 text-slate-800 font-mono text-xs rounded-lg overflow-x-auto">
                  {inspectingItem.raw_content}
                </pre>
              </div>
            </div>
            <div className="p-4 bg-slate-50 border-t flex justify-end">
              <button
                onClick={() => setInspectingItem(null)}
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-700 transition"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Mapping Dialog Modal */}
      {mappingItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
          <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden animate-in fade-in zoom-in-95 duration-150">
            <div className="p-5 border-b flex items-center justify-between">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <LinkIcon className="h-5 w-5 text-indigo-600" />
                Vincular à Execução de Ensaio
              </h3>
              <button
                onClick={() => setMappingItem(null)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>
            <div className="p-5 space-y-4">
              <p className="text-sm text-slate-600">
                Os dados brutos parseados serão injetados diretamente na execução selecionada, eliminando transcrições manuais.
              </p>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  UUID da Execução de Ensaio Alvo (TestExecution ID) *
                </label>
                <input
                  type="text"
                  value={mapExecutionId}
                  onChange={(e) => setMapExecutionId(e.target.value.trim())}
                  required
                  placeholder="ex.: 8dd52f14-4df5-4c24-8ca1-95b853edd9f7"
                  className="w-full font-mono text-sm rounded-lg border border-slate-300 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Copie o identificador da execução na bancada de ensaios ou informe o UUID de destino.
                </p>
              </div>
            </div>
            <div className="p-4 bg-slate-50 border-t flex justify-end gap-2">
              <button
                onClick={() => setMappingItem(null)}
                className="px-4 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-200 transition"
              >
                Cancelar
              </button>
              <button
                onClick={handleMapExecution}
                disabled={submitting || !mapExecutionId}
                className="px-4 py-2 text-sm font-semibold rounded-lg text-white bg-indigo-600 hover:bg-indigo-700 shadow transition disabled:opacity-50"
              >
                Confirmar Mapeamento
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
