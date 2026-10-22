/**
 * ==============================================================================
 * 广州电动自行车 30km/h 巡航预警雷达核心算法库 (Rider Radar Core Algorithms)
 * 
 * 模块包含：
 * 1. PointDirectionParser: 点位语义方向智能识别与过滤（东往西、西往东、南往北、北往南、X行等）
 * 2. SpeedAdaptiveWarningEngine: 车速自适应动态预警距离算法（稳定 12~15 秒提前量，60m~180m 限幅平滑）
 * 3. HeadingFilterAndLockEngine: GPS 航向抗抖动与静止锁存算法（<3km/h 零速锁存，单位向量圆周平滑滤波）
 * 4. CruiseRadarFilterManager: 统一调度与对外高阶集成接口
 * ==============================================================================
 */

(function (global, factory) {
  if (typeof module === 'object' && typeof module.exports === 'object') {
    module.exports = factory();
  } else {
    global.RiderRadarAlgo = factory();
  }
})(typeof window !== 'undefined' ? window : this, function () {
  'use strict';

  /* ============================================================================
   * 基础数学与几何辅助函数
   * ============================================================================ */
  const MathUtils = {
    DEG_TO_RAD: Math.PI / 180,
    RAD_TO_DEG: 180 / Math.PI,
    EARTH_RADIUS: 6371000, // 地球平均半径 (米)

    /** 计算两点大圆距离 (Haversine 算法, 单位: 米) */
    getDistance: function (lat1, lon1, lat2, lon2) {
      const dLat = (lat2 - lat1) * MathUtils.DEG_TO_RAD;
      const dLon = (lon2 - lon1) * MathUtils.DEG_TO_RAD;
      const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1 * MathUtils.DEG_TO_RAD) * Math.cos(lat2 * MathUtils.DEG_TO_RAD) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
      return MathUtils.EARTH_RADIUS * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    },

    /** 计算航向角 Azimuth/Bearing (0°=正北, 90°=正东, 180°=正南, 270°=正西) */
    getBearing: function (lat1, lon1, lat2, lon2) {
      const φ1 = lat1 * MathUtils.DEG_TO_RAD;
      const φ2 = lat2 * MathUtils.DEG_TO_RAD;
      const Δλ = (lon2 - lon1) * MathUtils.DEG_TO_RAD;
      const y = Math.sin(Δλ) * Math.cos(φ2);
      const x = Math.cos(φ1) * Math.sin(φ2) - Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
      const θ = Math.atan2(y, x);
      return (θ * MathUtils.RAD_TO_DEG + 360) % 360;
    },

    /** 计算两个角度在圆周上的最小绝对差值 [0°, 180°] */
    getAngleDiff: function (a, b) {
      const diff = Math.abs(a - b) % 360;
      return diff > 180 ? 360 - diff : diff;
    },

    /** 角度转中文方位描述 */
    headingToText: function (deg) {
      const dirs = ['正北', '东北', '正东', '东南', '正南', '西南', '正西', '西北'];
      const index = Math.round(((deg % 360) + 360) % 360 / 45) % 8;
      return `${dirs[index]} ${Math.round(deg)}°`;
    },

    /** 数值限幅 Clamp */
    clamp: function (val, min, max) {
      return Math.max(min, Math.min(max, val));
    }
  };

  /* ============================================================================
   * 1. 点位语义方向智能识别与过滤引擎 (PointDirectionParser)
   * ============================================================================ */
  const CARDINAL_HEADINGS = {
    '北': 0,
    '东北': 45,
    '东': 90,
    '东南': 135,
    '南': 180,
    '西南': 225,
    '西': 270,
    '西北': 315
  };

  class PointDirectionParser {
    constructor() {
      // 高性能 LRU / 内存缓存，避免高频匹配重复点位标题
      this.cache = new Map();

      // 正则1: 配对模式 "(由)?A往/向/至/到B" (例如: 东往西, 西向东, 由南向北, 东北往西南)
      // 注意: 受控行驶方向为 B (目的地指向)
      this.regexPair = /(?:由)?(东北|东南|西北|西南|东|南|西|北)[往至到向](东北|东南|西北|西南|东|南|西|北)/g;

      // 正则2: 单向行进模式 "X行" (例如: 东行, 西行, 南行, 北行)
      this.regexXing = /(东北|东南|西北|西南|东|南|西|北)行/g;

      // 正则3: 括号内显式方向 "(往东)", "(向西)", "(朝北)"
      this.regexParenSingle = /[（(](?:往|向|朝)?(东北|东南|西北|西南|东|南|西|北)[)）]/;

      // 正则4: 双向/全向标示
      this.regexBi = /双向/;
    }

    /**
     * 高性能解析点位标题中的受控方向语义
     * @param {string} title 点位名称 (例如: "东风中路盘福立交下桥位(东往西)")
     * @returns {Object} {
     *    directionText: string,      // "东往西" | "西行" | "全向/路口" | "双向"
     *    controlledHeading: number,  // 0~360 (受控车头航向，例如 270° 代表西行车道)
     *    isOmnidirectional: boolean, // 是否全向/路口
     *    toleranceDeg: number        // 容差角，默认 45°
     * }
     */
    parsePointDirection(title) {
      if (!title || typeof title !== 'string') {
        return {
          directionText: '全向/未标明',
          controlledHeading: null,
          isOmnidirectional: true,
          toleranceDeg: 180
        };
      }

      if (this.cache.has(title)) {
        return this.cache.get(title);
      }

      // 1. 检查双向标示
      if (this.regexBi.test(title)) {
        const res = {
          directionText: '双向',
          controlledHeading: null,
          isOmnidirectional: true,
          toleranceDeg: 180
        };
        this.cache.set(title, res);
        return res;
      }

      // 2. 匹配 "A往B" 模式。若有多个匹配（如长路名中嵌套），取最后一个匹配（即末尾限定修饰语）
      this.regexPair.lastIndex = 0;
      let mPair = null;
      let match;
      while ((match = this.regexPair.exec(title)) !== null) {
        mPair = match;
      }

      if (mPair) {
        const fromDir = mPair[1];
        const toDir = mPair[2];
        const heading = CARDINAL_HEADINGS[toDir];
        const res = {
          directionText: `${fromDir}往${toDir}`,
          fromDir: fromDir,
          toDir: toDir,
          controlledHeading: heading, // 东往西 => 西 (270°)
          isOmnidirectional: false,
          toleranceDeg: 45
        };
        this.cache.set(title, res);
        return res;
      }

      // 3. 匹配 "X行" 模式 (东行 => 90°)
      this.regexXing.lastIndex = 0;
      let mXing = null;
      while ((match = this.regexXing.exec(title)) !== null) {
        mXing = match;
      }

      if (mXing) {
        const toDir = mXing[1];
        const heading = CARDINAL_HEADINGS[toDir];
        const res = {
          directionText: `${toDir}行`,
          fromDir: null,
          toDir: toDir,
          controlledHeading: heading,
          isOmnidirectional: false,
          toleranceDeg: 45
        };
        this.cache.set(title, res);
        return res;
      }

      // 4. 匹配括号内单向 "(往东)", "(向北)"
      const mParen = this.regexParenSingle.exec(title);
      if (mParen) {
        const toDir = mParen[1];
        const heading = CARDINAL_HEADINGS[toDir];
        const res = {
          directionText: `往${toDir}`,
          fromDir: null,
          toDir: toDir,
          controlledHeading: heading,
          isOmnidirectional: false,
          toleranceDeg: 45
        };
        this.cache.set(title, res);
        return res;
      }

      // 5. 无显式方向限定的十字路口或路段 (例如 "东风中路仓边路路口")，按全向处理
      const res = {
        directionText: '全向/路口',
        fromDir: null,
        toDir: null,
        controlledHeading: null,
        isOmnidirectional: true,
        toleranceDeg: 180
      };
      this.cache.set(title, res);
      return res;
    }

    /**
     * 比对当前骑行航向与点位受控航向
     * @param {number} riderHeading 骑手当前车头航向 (0°~360°)
     * @param {Object|string} pointDirection 点位解析结果或标题
     * @param {number} [customTolerance=45] 自定义同向容差角度
     * @returns {Object} {
     *    shouldAlert: boolean,       // 是否允许触发预警 (同向或全向为 true，对向为 false)
     *    relation: string,           // 'same_direction' | 'opposite_direction' | 'cross_direction' | 'omnidirectional'
     *    angleDiff: number,          // 航向偏差角 (0°~180°)
     *    reason: string              // 人类可读判断原因
     * }
     */
    evaluateRiderHeading(riderHeading, pointDirection, customTolerance = 45) {
      const dirInfo = typeof pointDirection === 'string'
        ? this.parsePointDirection(pointDirection)
        : pointDirection;

      if (!dirInfo || dirInfo.isOmnidirectional || dirInfo.controlledHeading === null) {
        return {
          shouldAlert: true,
          relation: 'omnidirectional',
          angleDiff: 0,
          reason: '全向/十字路口监控点，全航向受控'
        };
      }

      const diff = MathUtils.getAngleDiff(riderHeading, dirInfo.controlledHeading);
      const tolerance = dirInfo.toleranceDeg || customTolerance;

      if (diff <= tolerance) {
        return {
          shouldAlert: true,
          relation: 'same_direction',
          angleDiff: Math.round(diff),
          reason: `同向行驶 (航向角偏差 ${Math.round(diff)}° ≤ 容差 ${tolerance}°)，触发核心预警`
        };
      } else if (diff >= 135) {
        return {
          shouldAlert: false,
          relation: 'opposite_direction',
          angleDiff: Math.round(diff),
          reason: `对向车道行驶 (航向角偏差 ${Math.round(diff)}° ≥ 135°)，反向静音过滤`
        };
      } else {
        return {
          shouldAlert: false,
          relation: 'cross_direction',
          angleDiff: Math.round(diff),
          reason: `横向/非受控车道 (航向角偏差 ${Math.round(diff)}°)，侧向静音过滤`
        };
      }
    }
  }

  /* ============================================================================
   * 2. 车速自适应预警距离算法引擎 (SpeedAdaptiveWarningEngine)
   * ============================================================================ */
  class SpeedAdaptiveWarningEngine {
    /**
     * @param {Object} [options]
     * @param {number} [options.targetLeadTimeSec=13.5] 期望提前量时间窗口 (12.0~15.0 秒)
     * @param {number} [options.minDistanceMeters=60.0] 最小预警距离下限 (米)
     * @param {number} [options.maxDistanceMeters=180.0] 最大预警距离上限 (米)
     * @param {number} [options.reactionBufferMeters=8.0] 骑手反应与系统延迟缓冲区 (米)
     * @param {number} [options.speedAlpha=0.25] 车速一阶低通滤波系数
     * @param {number} [options.maxDistanceSlewRate=15.0] 预警距离每秒最大变化量 (米/秒)，防视觉抖动
     */
    constructor(options = {}) {
      this.targetLeadTimeSec = options.targetLeadTimeSec || 13.5;
      this.minDistanceMeters = options.minDistanceMeters || 60.0;
      this.maxDistanceMeters = options.maxDistanceMeters || 180.0;
      this.reactionBufferMeters = options.reactionBufferMeters || 8.0;
      this.speedAlpha = options.speedAlpha || 0.25;
      this.maxDistanceSlewRate = options.maxDistanceSlewRate || 15.0;

      this.filteredSpeedKmh = 0.0;
      this.currentDistance = this.minDistanceMeters;
      this.lastTimestamp = 0;
    }

    /** 静态数学计算纯函数: 给定车速直接推导理论预警距离 */
    static computeIdealDistance(speedKmh, leadTime = 13.5, minDist = 60, maxDist = 180, buffer = 8) {
      const speedMs = Math.max(0, speedKmh) / 3.6;
      const nominal = speedMs * leadTime + buffer;
      return MathUtils.clamp(nominal, minDist, maxDist);
    }

    /**
     * 周期性更新车速并返回平滑后的自适应预警距离
     * @param {number} rawSpeedKmh 实时原始车速 (km/h)
     * @param {number} [timestampMs] 时间戳
     * @returns {Object} {
     *    warningDistance: number,    // 取整预警距离 (米)
     *    exactDistance: number,      // 浮点连续距离
     *    filteredSpeedKmh: number,   // 低通滤波后平滑车速
     *    leadTimeSec: number         // 实际提前量秒数
     * }
     */
    update(rawSpeedKmh, timestampMs = Date.now()) {
      const safeRawSpeed = Math.max(0, typeof rawSpeedKmh === 'number' && !isNaN(rawSpeedKmh) ? rawSpeedKmh : 0);

      if (this.lastTimestamp === 0) {
        this.lastTimestamp = timestampMs;
        this.filteredSpeedKmh = safeRawSpeed;
        this.currentDistance = SpeedAdaptiveWarningEngine.computeIdealDistance(
          this.filteredSpeedKmh,
          this.targetLeadTimeSec,
          this.minDistanceMeters,
          this.maxDistanceMeters,
          this.reactionBufferMeters
        );
        return this._formatResult();
      }

      const dt = MathUtils.clamp((timestampMs - this.lastTimestamp) / 1000, 0.02, 1.0);
      this.lastTimestamp = timestampMs;

      // 1. 车速 EMA 一阶低通滤波，抑制瞬时传感器毛刺
      this.filteredSpeedKmh = this.filteredSpeedKmh * (1 - this.speedAlpha) + safeRawSpeed * this.speedAlpha;

      // 2. 依据当前平滑车速计算目标预警距离
      const targetDist = SpeedAdaptiveWarningEngine.computeIdealDistance(
        this.filteredSpeedKmh,
        this.targetLeadTimeSec,
        this.minDistanceMeters,
        this.maxDistanceMeters,
        this.reactionBufferMeters
      );

      // 3. 预警距离斜率限制器 (Slew-rate Limiter)
      // 避免雷达扇区在突然急刹或大油门时剧烈伸缩造成视觉眩目
      const maxDelta = this.maxDistanceSlewRate * dt;
      const delta = targetDist - this.currentDistance;
      if (Math.abs(delta) > maxDelta) {
        this.currentDistance += Math.sign(delta) * maxDelta;
      } else {
        this.currentDistance = targetDist;
      }

      return this._formatResult();
    }

    _formatResult() {
      const speedMs = this.filteredSpeedKmh / 3.6;
      const leadTime = speedMs > 0.5 ? (this.currentDistance / speedMs).toFixed(1) : '充足(低速)';
      return {
        warningDistance: Math.round(this.currentDistance),
        exactDistance: parseFloat(this.currentDistance.toFixed(1)),
        filteredSpeedKmh: parseFloat(this.filteredSpeedKmh.toFixed(1)),
        leadTimeSec: leadTime
      };
    }

    /** 重置引擎状态 */
    reset(initialSpeedKmh = 0) {
      this.filteredSpeedKmh = Math.max(0, initialSpeedKmh);
      this.currentDistance = SpeedAdaptiveWarningEngine.computeIdealDistance(
        this.filteredSpeedKmh,
        this.targetLeadTimeSec,
        this.minDistanceMeters,
        this.maxDistanceMeters,
        this.reactionBufferMeters
      );
      this.lastTimestamp = 0;
    }
  }

  /* ============================================================================
   * 3. GPS 航向抗抖动与静止滤波引擎 (HeadingFilterAndLockEngine)
   * ============================================================================ */
  class HeadingFilterAndLockEngine {
    /**
     * @param {Object} [options]
     * @param {number} [options.stopSpeedThreshold=3.0] 静止判据阈值 (km/h)，低于此速度触发航向锁存
     * @param {number} [options.moveSpeedThreshold=4.5] 运动判据阈值 (km/h)，高于此速度且有位移解除锁存
     * @param {number} [options.minMoveDistanceMeters=2.5] 坐标推算航向所需最小位移基线 (米)
     * @param {number} [options.minAlpha=0.15] 低速重度滤波平滑系数 (阻尼大，抗漂移)
     * @param {number} [options.maxAlpha=0.45] 巡航灵敏平滑系数 (跟转及时，无迟滞)
     */
    constructor(options = {}) {
      this.stopSpeedThreshold = options.stopSpeedThreshold || 3.0;
      this.moveSpeedThreshold = options.moveSpeedThreshold || 4.5;
      this.minMoveDistanceMeters = options.minMoveDistanceMeters || 2.5;
      this.minAlpha = options.minAlpha || 0.15;
      this.maxAlpha = options.maxAlpha || 0.45;

      // 状态变量
      this.isStationary = true;
      this.heading = 0; // 当前滤波航向 [0°, 360°)
      this.lastCruisingHeading = 0; // 巡航航向锁存值
      this.lastPosition = null; // 上一次有效地理坐标 { lat, lng }
      this.lastSampleTime = 0;

      // 二维单位向量 [sin(θ), cos(θ)]，彻底消除 0°/360° 跨界数值突变
      this.vecX = 0; // East分量 (sin)
      this.vecY = 1; // North分量 (cos)
      this.initialized = false;
    }

    /** 初始化基准航向与坐标 */
    init(initialHeading = 0, initialPos = null) {
      this.heading = (initialHeading % 360 + 360) % 360;
      this.lastCruisingHeading = this.heading;
      const rad = this.heading * MathUtils.DEG_TO_RAD;
      this.vecX = Math.sin(rad);
      this.vecY = Math.cos(rad);
      if (initialPos && typeof initialPos.lat === 'number') {
        this.lastPosition = { lat: initialPos.lat, lng: initialPos.lng };
      }
      this.initialized = true;
      this.isStationary = true;
    }

    /**
     * 周期性输入 GPS 定位样本，输出高抗噪平滑航向
     * @param {Object} sample
     * @param {number} sample.lat GCJ-02 或 WGS-84 纬度
     * @param {number} sample.lng GCJ-02 或 WGS-84 经度
     * @param {number} [sample.speedKmh] 实时车速 (km/h)
     * @param {number|null} [sample.rawHeading] 手机硬件 GPS 航向 (0°~360°)，可能为 null 或 NaN
     * @param {number} [sample.timestampMs] 时间戳
     * @returns {Object} {
     *    heading: number,            // 平滑滤波后航向 (0.0° ~ 359.9°)
     *    state: string,              // 'LOCKED_STATIONARY' | 'ACTIVE_TRACKING' | 'COASTING'
     *    isLocked: boolean,          // 是否处于静止锁存状态
     *    speedKmh: number,           // 评估车速
     *    headingSource: string       // 'latch' | 'gps_sensor' | 'trajectory_bearing'
     * }
     */
    update(sample) {
      const { lat, lng, speedKmh, rawHeading, timestampMs } = sample;
      const currentSpeed = Math.max(0, typeof speedKmh === 'number' && !isNaN(speedKmh) ? speedKmh : 0);

      if (!this.initialized) {
        const initH = (typeof rawHeading === 'number' && !isNaN(rawHeading) && rawHeading >= 0) ? rawHeading : 0;
        this.init(initH, { lat, lng });
        return {
          heading: Math.round(this.heading * 10) / 10,
          state: 'INITIALIZED',
          isLocked: this.isStationary,
          speedKmh: currentSpeed,
          headingSource: 'initial'
        };
      }

      // 1. 计算与上一位置的位移距离
      let displacement = 0;
      if (this.lastPosition) {
        displacement = MathUtils.getDistance(this.lastPosition.lat, this.lastPosition.lng, lat, lng);
      }

      // 2. 带滞回区（Hysteresis）的静止检测状态机
      // 防止在 3.0km/h 边界频繁抖动切态
      if (this.isStationary) {
        // 解除锁存条件: 车速恢复且真实位移超过置信门限
        if (currentSpeed >= this.moveSpeedThreshold && displacement >= this.minMoveDistanceMeters) {
          this.isStationary = false;
        }
      } else {
        // 进入锁存条件: 车速降低至停止门限
        if (currentSpeed < this.stopSpeedThreshold) {
          this.isStationary = true;
          this.lastCruisingHeading = this.heading; // 锁存最后一刻有效的巡航车头方向
        }
      }

      // 3. 静止/红绿灯等候状态：激活静止锁存算法
      // 彻底无视 GPS 静态漂移和零速传感器噪声
      if (this.isStationary) {
        return {
          heading: Math.round(this.lastCruisingHeading * 10) / 10,
          state: 'LOCKED_STATIONARY',
          isLocked: true,
          speedKmh: currentSpeed,
          headingSource: 'latch'
        };
      }

      // 4. 行驶状态：甄选高置信度测量航向 candidate
      let targetHeading = null;
      let headingSource = 'none';

      // 优选通道 A: 手机系统硬件/融合定位高频航向 (iOS/Android 内置高精度航向)
      if (typeof rawHeading === 'number' && !isNaN(rawHeading) && rawHeading >= 0) {
        targetHeading = (rawHeading % 360 + 360) % 360;
        headingSource = 'gps_sensor';
      }
      // 优选通道 B: 若无硬件航向，且位移足够清晰（>=2.5m），通过前后坐标方位角推算
      else if (this.lastPosition && displacement >= this.minMoveDistanceMeters) {
        targetHeading = MathUtils.getBearing(this.lastPosition.lat, this.lastPosition.lng, lat, lng);
        headingSource = 'trajectory_bearing';
      }

      // 若本采样周期无有效观测源，维持惯性航向
      if (targetHeading === null) {
        return {
          heading: Math.round(this.heading * 10) / 10,
          state: 'COASTING',
          isLocked: false,
          speedKmh: currentSpeed,
          headingSource: 'coasting'
        };
      }

      // 刷新上一基准坐标
      this.lastPosition = { lat, lng };

      // 5. 车速自适应平滑加权系数 (Speed-adaptive alpha)
      // 5km/h 蠕行: alpha ~ 0.15 (抑制抖动)
      // 30km/h 巡航: alpha ~ 0.45 (敏捷跟踪道路转向)
      const speedRatio = MathUtils.clamp((currentSpeed - this.stopSpeedThreshold) / 27.0, 0.0, 1.0);
      const alpha = this.minAlpha + (this.maxAlpha - this.minAlpha) * speedRatio;

      // 6. 核心：单位圆周向量低通滤波 (Unit Vector Low-Pass Filter)
      // 巧妙将角度映射至 (cos, sin) 空间，完美解决 359° 与 1° 之间的跨界平均灾难
      const targetRad = targetHeading * MathUtils.DEG_TO_RAD;
      const targetX = Math.sin(targetRad);
      const targetY = Math.cos(targetRad);

      this.vecX = (1 - alpha) * this.vecX + alpha * targetX;
      this.vecY = (1 - alpha) * this.vecY + alpha * targetY;

      // 归一化单位向量
      const norm = Math.hypot(this.vecX, this.vecY);
      if (norm > 1e-6) {
        this.vecX /= norm;
        this.vecY /= norm;
      }

      // 映射回导航角 [0°, 360°)
      const filteredAngle = Math.atan2(this.vecX, this.vecY) * MathUtils.RAD_TO_DEG;
      this.heading = (filteredAngle + 360) % 360;
      this.lastCruisingHeading = this.heading;

      return {
        heading: Math.round(this.heading * 10) / 10,
        state: 'ACTIVE_TRACKING',
        isLocked: false,
        speedKmh: currentSpeed,
        headingSource: headingSource
      };
    }
  }

  /* ============================================================================
   * 4. 巡航雷达统一调度管理器 (CruiseRadarFilterManager)
   * 将方向识别、车速自适应距离、航向抗抖滤波统一封装，便于业务端一行代码接入
   * ============================================================================ */
  class CruiseRadarFilterManager {
    constructor(options = {}) {
      this.directionParser = new PointDirectionParser();
      this.speedEngine = new SpeedAdaptiveWarningEngine(options.speedOptions);
      this.headingEngine = new HeadingFilterAndLockEngine(options.headingOptions);
      this.fovAngle = options.fovAngle || 40; // 探测锥半角 (±40°)
    }

    /**
     * 处理一次 GPS 采样并更新内部物理状态
     * @param {Object} gpsData { lat, lng, speedKmh, rawHeading, timestampMs }
     * @returns {Object} 当前平滑车况状态
     */
    processGPSUpdate(gpsData) {
      const headingResult = this.headingEngine.update(gpsData);
      const speedResult = this.speedEngine.update(gpsData.speedKmh, gpsData.timestampMs);

      return {
        lat: gpsData.lat,
        lng: gpsData.lng,
        heading: headingResult.heading,
        headingState: headingResult.state,
        isHeadingLocked: headingResult.isLocked,
        speedKmh: speedResult.filteredSpeedKmh,
        warningDistance: speedResult.warningDistance,
        leadTimeSec: speedResult.leadTimeSec
      };
    }

    /**
     * 对候选点位集进行空间与语义方向双重碰撞筛选
     * @param {Object} vehicleState 当前车辆状态 (由 processGPSUpdate 输出)
     * @param {Array<Array>} pointsArray 点位数组 [[lat, lng, title, ...], ...]
     * @returns {Object|null} 最佳预警目标或 null
     */
    evaluateTargets(vehicleState, pointsArray) {
      const { lat, lng, heading, warningDistance } = vehicleState;
      let closestTarget = null;
      let minDistance = Infinity;

      for (let i = 0; i < pointsArray.length; i++) {
        const pt = pointsArray[i];
        // 粗筛：经纬度粗糙包围盒 (约 200米外直接丢弃，极大减轻计算量)
        if (Math.abs(pt[0] - lat) > 0.003 || Math.abs(pt[1] - lng) > 0.003) {
          continue;
        }

        const dist = MathUtils.getDistance(lat, lng, pt[0], pt[1]);
        if (dist > warningDistance) continue;

        // 计算车头指向该点的相对方位角
        const bearingToPt = MathUtils.getBearing(lat, lng, pt[0], pt[1]);
        const angleOffset = MathUtils.getAngleDiff(heading, bearingToPt);

        // 几何锥体筛选：点位必须处于车头前方扇区 (<= FOV)
        if (angleOffset > this.fovAngle) continue;

        // 核心亮点：语义方向校验（过滤对向车道）
        const title = pt[2] || '';
        const dirInfo = this.directionParser.parsePointDirection(title);
        const matchResult = this.directionParser.evaluateRiderHeading(heading, dirInfo);

        // 若判断为对向车道（反向），坚决抑制，不触发主预警！
        if (!matchResult.shouldAlert) {
          continue;
        }

        if (dist < minDistance) {
          minDistance = dist;
          const speedMs = Math.max(vehicleState.speedKmh / 3.6, 2.0);
          closestTarget = {
            index: i,
            lat: pt[0],
            lng: pt[1],
            title: title,
            distance: Math.round(dist),
            angleOffset: Math.round(angleOffset),
            etaSec: Math.round(dist / speedMs),
            directionInfo: dirInfo,
            matchResult: matchResult
          };
        }
      }

      return closestTarget;
    }
  }

  // 导出算法套件
  return {
    MathUtils: MathUtils,
    PointDirectionParser: PointDirectionParser,
    SpeedAdaptiveWarningEngine: SpeedAdaptiveWarningEngine,
    HeadingFilterAndLockEngine: HeadingFilterAndLockEngine,
    CruiseRadarFilterManager: CruiseRadarFilterManager
  };
});
