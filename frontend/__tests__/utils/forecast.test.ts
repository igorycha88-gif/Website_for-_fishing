import {
  getMoonPhaseType,
  getBiteScoreLabel,
  getBiteScoreColor,
  getBiteScoreTextColor,
  getMoonPhaseLabel,
  getMoonPhaseTooltip,
} from "@/types/forecast";

describe("getMoonPhaseType", () => {
  it("returns empty string for null", () => {
    expect(getMoonPhaseType(null)).toBe("");
  });

  it("returns 'Новолуние' for phase 0", () => {
    expect(getMoonPhaseType(0)).toBe("Новолуние");
  });

  it("returns 'Новолуние' for phase 0.05", () => {
    expect(getMoonPhaseType(0.05)).toBe("Новолуние");
  });

  it("returns 'Новолуние' for phase 0.95", () => {
    expect(getMoonPhaseType(0.95)).toBe("Новолуние");
  });

  it("returns 'Новолуние' for phase 1.0", () => {
    expect(getMoonPhaseType(1.0)).toBe("Новолуние");
  });

  it("returns 'Растущая' for phase 0.1", () => {
    expect(getMoonPhaseType(0.1)).toBe("Растущая");
  });

  it("returns 'Растущая' for phase 0.25", () => {
    expect(getMoonPhaseType(0.25)).toBe("Растущая");
  });

  it("returns 'Растущая' for phase 0.44", () => {
    expect(getMoonPhaseType(0.44)).toBe("Растущая");
  });

  it("returns 'Полнолуние' for phase 0.45", () => {
    expect(getMoonPhaseType(0.45)).toBe("Полнолуние");
  });

  it("returns 'Полнолуние' for phase 0.5", () => {
    expect(getMoonPhaseType(0.5)).toBe("Полнолуние");
  });

  it("returns 'Полнолуние' for phase 0.55", () => {
    expect(getMoonPhaseType(0.55)).toBe("Полнолуние");
  });

  it("returns 'Убывающая' for phase 0.56", () => {
    expect(getMoonPhaseType(0.56)).toBe("Убывающая");
  });

  it("returns 'Убывающая' for phase 0.75", () => {
    expect(getMoonPhaseType(0.75)).toBe("Убывающая");
  });

  it("returns 'Убывающая' for phase 0.94", () => {
    expect(getMoonPhaseType(0.94)).toBe("Убывающая");
  });
});

describe("getBiteScoreLabel", () => {
  it("returns 'Отлично' for score 80-100", () => {
    expect(getBiteScoreLabel(80)).toBe("Отлично");
    expect(getBiteScoreLabel(90)).toBe("Отлично");
    expect(getBiteScoreLabel(100)).toBe("Отлично");
  });

  it("returns 'Хорошо' for score 65-79", () => {
    expect(getBiteScoreLabel(65)).toBe("Хорошо");
    expect(getBiteScoreLabel(70)).toBe("Хорошо");
    expect(getBiteScoreLabel(79)).toBe("Хорошо");
  });

  it("returns 'Умеренно' for score 50-64", () => {
    expect(getBiteScoreLabel(50)).toBe("Умеренно");
    expect(getBiteScoreLabel(55)).toBe("Умеренно");
    expect(getBiteScoreLabel(64)).toBe("Умеренно");
  });

  it("returns 'Слабо' for score 35-49", () => {
    expect(getBiteScoreLabel(35)).toBe("Слабо");
    expect(getBiteScoreLabel(40)).toBe("Слабо");
    expect(getBiteScoreLabel(49)).toBe("Слабо");
  });

  it("returns 'Плохо' for score 0-34", () => {
    expect(getBiteScoreLabel(0)).toBe("Плохо");
    expect(getBiteScoreLabel(20)).toBe("Плохо");
    expect(getBiteScoreLabel(34)).toBe("Плохо");
  });
});

describe("getBiteScoreColor", () => {
  it("returns correct color for each range", () => {
    expect(getBiteScoreColor(80)).toBe("bg-green-500");
    expect(getBiteScoreColor(65)).toBe("bg-yellow-500");
    expect(getBiteScoreColor(50)).toBe("bg-orange-500");
    expect(getBiteScoreColor(35)).toBe("bg-red-400");
    expect(getBiteScoreColor(0)).toBe("bg-red-600");
  });
});

describe("getBiteScoreTextColor", () => {
  it("returns correct text color for each range", () => {
    expect(getBiteScoreTextColor(80)).toBe("text-green-600");
    expect(getBiteScoreTextColor(65)).toBe("text-yellow-600");
    expect(getBiteScoreTextColor(50)).toBe("text-orange-600");
    expect(getBiteScoreTextColor(35)).toBe("text-red-500");
    expect(getBiteScoreTextColor(0)).toBe("text-red-700");
  });
});

describe("getMoonPhaseLabel", () => {
  it("returns empty string for null", () => {
    expect(getMoonPhaseLabel(null)).toBe("");
  });

  it("returns correct label for new moon", () => {
    expect(getMoonPhaseLabel(0)).toContain("Новолуние");
  });

  it("returns correct label for full moon", () => {
    expect(getMoonPhaseLabel(0.5)).toContain("Полнолуние");
  });
});

describe("getMoonPhaseTooltip", () => {
  it("returns empty string for null", () => {
    expect(getMoonPhaseTooltip(null)).toBe("");
  });

  it("returns tooltip for Новолуние (phase 0)", () => {
    expect(getMoonPhaseTooltip(0)).toBe("🌑 Новолуние. Хорошее время для ночной рыбалки. Рыба активна.");
  });

  it("returns tooltip for Новолуние (phase 0.05)", () => {
    expect(getMoonPhaseTooltip(0.05)).toBe("🌑 Новолуние. Хорошее время для ночной рыбалки. Рыба активна.");
  });

  it("returns tooltip for Новолуние (phase 0.95)", () => {
    expect(getMoonPhaseTooltip(0.95)).toBe("🌑 Новолуние. Хорошее время для ночной рыбалки. Рыба активна.");
  });

  it("returns tooltip for Растущая (phase 0.1)", () => {
    expect(getMoonPhaseTooltip(0.1)).toBe("🌒 Растущая луна. Благоприятно для хищной рыбы.");
  });

  it("returns tooltip for Растущая (phase 0.3)", () => {
    expect(getMoonPhaseTooltip(0.3)).toBe("🌒 Растущая луна. Благоприятно для хищной рыбы.");
  });

  it("returns tooltip for Полнолуние (phase 0.5)", () => {
    expect(getMoonPhaseTooltip(0.5)).toBe("🌕 Полнолуние. Рыба может быть пассивной. Лучше рыбачить утром.");
  });

  it("returns tooltip for Убывающая (phase 0.6)", () => {
    expect(getMoonPhaseTooltip(0.6)).toBe("🌗 Убывающая луна. Хороший клев белой рыбы.");
  });

  it("returns tooltip for Убывающая (phase 0.9)", () => {
    expect(getMoonPhaseTooltip(0.9)).toBe("🌗 Убывающая луна. Хороший клев белой рыбы.");
  });
});
