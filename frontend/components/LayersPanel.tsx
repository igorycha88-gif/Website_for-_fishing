"use client";

import { Layers, Waves, Tag, Palette } from "lucide-react";
import type { DepthLayerConfig, ColorScheme } from "@/types/depth";

interface LayersPanelProps {
  config: DepthLayerConfig;
  onChange: (config: DepthLayerConfig) => void;
}

const COLOR_SCHEMES: Record<ColorScheme, { range: string; color: string }[]> = {
  navionics: [
    { range: "0-2м", color: "#B3E5FC" },
    { range: "2-5м", color: "#4FC3F7" },
    { range: "5-10м", color: "#0288D1" },
    { range: "10-20м", color: "#01579B" },
    { range: "20-50м", color: "#1A237E" },
    { range: ">50м", color: "#000C2E" },
  ],
  contrast: [
    { range: "0-2м", color: "#80DEEA" },
    { range: "2-5м", color: "#26C6DA" },
    { range: "5-10м", color: "#00ACC1" },
    { range: "10-20м", color: "#00838F" },
    { range: "20-50м", color: "#006064" },
    { range: ">50м", color: "#00363A" },
  ],
  sport: [
    { range: "0-2м", color: "#A5D6A7" },
    { range: "2-5м", color: "#66BB6A" },
    { range: "5-10м", color: "#43A047" },
    { range: "10-20м", color: "#2E7D32" },
    { range: "20-50м", color: "#1B5E20" },
    { range: ">50м", color: "#0D3811" },
  ],
};

const SCHEME_LABELS: Record<ColorScheme, string> = {
  navionics: "Navionics",
  contrast: "Контраст",
  sport: "Спорт",
};

export default function LayersPanel({ config, onChange }: LayersPanelProps) {
  const toggleDepth = () => {
    onChange({ ...config, enabled: !config.enabled });
  };

  const toggleIsobaths = () => {
    onChange({ ...config, showIsobaths: !config.showIsobaths });
  };

  const toggleLabels = () => {
    onChange({ ...config, showLabels: !config.showLabels });
  };

  const setOpacity = (opacity: number) => {
    onChange({ ...config, opacity });
  };

  const setScheme = (scheme: ColorScheme) => {
    onChange({ ...config, colorScheme: scheme });
  };

  const depthColors = COLOR_SCHEMES[config.colorScheme];

  return (
    <div
      className="absolute z-30 bg-white rounded-lg shadow-lg"
      style={{ top: "16px", left: "16px", width: "230px" }}
    >
      <div className="flex items-center gap-2 px-4 pt-3 pb-2 border-b border-gray-100">
        <Layers className="w-4 h-4 text-primary-sea" />
        <h3 className="text-sm font-bold text-gray-800">Слои карты</h3>
      </div>

      <div className="p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Waves className="w-4 h-4 text-blue-500" />
            <span className="text-sm text-gray-700">Глубины</span>
          </div>
          <button
            onClick={toggleDepth}
            className={`relative w-11 h-6 rounded-full transition-colors ${
              config.enabled ? "bg-primary-sea" : "bg-gray-300"
            }`}
            aria-label="Toggle depth layer"
          >
            <span
              className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${
                config.enabled ? "translate-x-5" : ""
              }`}
            />
          </button>
        </div>

        {config.enabled && (
          <>
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Прозрачность</span>
                <span>{Math.round(config.opacity * 100)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.opacity}
                onChange={(e) => setOpacity(parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-sea"
              />
            </div>

            <div className="space-y-1.5 pt-1">
              <div className="flex items-center gap-1.5 text-xs font-medium text-gray-600">
                <Palette className="w-3.5 h-3.5" />
                <span>Цветовая схема</span>
              </div>
              <div className="flex gap-1">
                {(Object.keys(SCHEME_LABELS) as ColorScheme[]).map((scheme) => (
                  <button
                    key={scheme}
                    onClick={() => setScheme(scheme)}
                    className={`flex-1 px-2 py-1.5 rounded text-xs font-medium transition-colors ${
                      config.colorScheme === scheme
                        ? "bg-primary-sea text-white"
                        : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                    }`}
                  >
                    {SCHEME_LABELS[scheme]}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5 pt-1">
              <div className="text-xs font-medium text-gray-600">
                Легенда глубин
              </div>
              <div className="grid grid-cols-1 gap-1">
                {depthColors.map((item) => (
                  <div
                    key={item.range}
                    className="flex items-center gap-2"
                  >
                    <div
                      className="w-4 h-4 rounded border border-gray-200"
                      style={{ backgroundColor: item.color }}
                    />
                    <span className="text-xs text-gray-600">{item.range}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-1 border-t border-gray-100 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-gray-500" />
                  <span className="text-xs text-gray-600">Метки глубин</span>
                </div>
                <button
                  onClick={toggleLabels}
                  className={`relative w-9 h-5 rounded-full transition-colors ${
                    config.showLabels ? "bg-primary-sea" : "bg-gray-300"
                  }`}
                  aria-label="Toggle depth labels"
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${
                      config.showLabels ? "translate-x-4" : ""
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">Изобаты (контуры)</span>
                <button
                  onClick={toggleIsobaths}
                  className={`relative w-9 h-5 rounded-full transition-colors ${
                    config.showIsobaths ? "bg-primary-sea" : "bg-gray-300"
                  }`}
                  aria-label="Toggle isobaths"
                >
                  <span
                    className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${
                      config.showIsobaths ? "translate-x-4" : ""
                    }`}
                  />
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
