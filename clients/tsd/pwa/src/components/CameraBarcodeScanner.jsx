import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import { BrowserMultiFormatReader, BarcodeFormat } from "@zxing/browser";
import { DecodeHintType } from "@zxing/library";
import {
  cardClass,
  iconButtonClass,
  inputClass,
  labelClass,
  mutedTextClass,
} from "../lib/ui";
import { cn } from "../lib/utils";

const ZXING_FORMATS = [
  BarcodeFormat.QR_CODE,
  BarcodeFormat.UPC_A,
  BarcodeFormat.UPC_E,
  BarcodeFormat.EAN_8,
  BarcodeFormat.EAN_13,
  BarcodeFormat.ITF,
  BarcodeFormat.PDF_417,
  BarcodeFormat.CODE_39,
  BarcodeFormat.CODE_128,
].filter(Boolean);

const PASSIVE_DECODE_ERRORS = new Set([
  "NotFoundException",
  "ChecksumException",
  "FormatException",
]);

const DEFAULT_CONSTRAINTS = {
  audio: false,
  video: {
    facingMode: { ideal: "environment" },
  },
};

const DEFAULT_LABELS = Object.freeze({
  camera: "Camera",
  cameraAuto: "Auto",
  hint: "Point the camera at the barcode",
  cancel: "Cancel",
});

const DEFAULT_ERROR_MESSAGES = Object.freeze({
  camera_not_supported: "Camera is not supported on this device",
  camera_permission_denied: "Camera access was denied",
  camera_not_found: "No suitable camera was found",
  camera_in_use: "Camera is already in use",
  camera_open_failed: "Unable to open the camera",
});

const ERROR_NAME_TO_KEY = {
  NotAllowedError: "camera_permission_denied",
  NotFoundError: "camera_not_found",
  OverconstrainedError: "camera_not_found",
  TrackStartError: "camera_in_use",
  NotReadableError: "camera_in_use",
};

const CameraBarcodeScanner = forwardRef(function CameraBarcodeScanner(
  {
    active = true,
    allowCameraSelection = true,
    autoHide = true,
    constraints = DEFAULT_CONSTRAINTS,
    containerId = "scanner",
    closeButtonId = "btn-close-scan",
    selectId = "camera-selector",
    videoId = "preview",
    className,
    videoClassName,
    controlsClassName,
    hintClassName,
    errorClassName,
    labels = {},
    errorMessages = {},
    formats = ZXING_FORMATS,
    readerOptions,
    onScan,
    onError,
    onScanningChange,
    onCameraChange,
    selectedCameraId: selectedCameraIdProp,
  },
  ref
) {
  const [scanning, setScanning] = useState(false);
  const [cameraOptions, setCameraOptions] = useState([]);
  const [selectedCameraIdState, setSelectedCameraIdState] = useState("default");
  const [cameraError, setCameraError] = useState(null);

  const readerRef = useRef(null);
  const readerControlsRef = useRef(null);
  const hintsRef = useRef(null);
  const videoRef = useRef(null);
  const lastResultRef = useRef(null);
  const selectedCameraRef = useRef("default");
  const scanningRef = useRef(false);

  const isControlled = selectedCameraIdProp != null;
  const currentSelectedCameraId = isControlled
    ? selectedCameraIdProp
    : selectedCameraIdState;

  const resolvedLabels = useMemo(
    () => ({ ...DEFAULT_LABELS, ...labels }),
    [labels]
  );

  const resolvedErrors = useMemo(
    () => ({ ...DEFAULT_ERROR_MESSAGES, ...errorMessages }),
    [errorMessages]
  );

  const captureInterval = readerOptions?.captureInterval ?? 150;
  const timeBetweenDecodingAttempts =
    readerOptions?.timeBetweenDecodingAttempts ?? 75;

  const clearError = useCallback(() => {
    setCameraError(null);
  }, []);

  const setScanningState = useCallback(
    (value) => {
      scanningRef.current = value;
      setScanning(value);
      if (typeof onScanningChange === "function") {
        onScanningChange(value);
      }
    },
    [onScanningChange]
  );

  const resolveErrorMessage = useCallback(
    (key) => {
      if (!key) return resolvedErrors.camera_open_failed;
      return resolvedErrors[key] ?? resolvedErrors.camera_open_failed;
    },
    [resolvedErrors]
  );

  const notifyError = useCallback(
    (key, error) => {
      const message = resolveErrorMessage(key);
      setCameraError(message);
      if (typeof onError === "function") {
        try {
          onError(message, { code: key, error });
        } catch (callbackError) {
          console.error(
            "[camera-scanner] onError callback failed",
            callbackError
          );
        }
      }
      return message;
    },
    [onError, resolveErrorMessage]
  );

  const updateCameraOptions = useCallback(async () => {
    if (!navigator?.mediaDevices?.enumerateDevices) {
      setCameraOptions([]);
      return [];
    }

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const videoDevices = devices.filter(
        (device) => device.kind === "videoinput"
      );
      setCameraOptions(videoDevices);

      const fallbackId = videoDevices[0]?.deviceId || "default";
      const nextId =
        currentSelectedCameraId === "default"
          ? currentSelectedCameraId
          : videoDevices.some(
              (device) => device.deviceId === currentSelectedCameraId
            )
          ? currentSelectedCameraId
          : fallbackId;

      if (!isControlled) {
        setSelectedCameraIdState(nextId);
      }

      if (nextId !== currentSelectedCameraId) {
        if (typeof onCameraChange === "function") {
          try {
            onCameraChange(nextId);
          } catch (err) {
            console.error(
              "[camera-scanner] onCameraChange callback failed",
              err
            );
          }
        }
      }

      return videoDevices;
    } catch (err) {
      console.warn("[camera-scanner] enumerate devices failed", err);
      setCameraOptions([]);
      return [];
    }
  }, [currentSelectedCameraId, isControlled, onCameraChange]);

  useEffect(() => {
    selectedCameraRef.current = currentSelectedCameraId;
  }, [currentSelectedCameraId]);

  const ensureReader = useCallback(() => {
    if (!readerRef.current) {
      const hints = new Map();
      if (DecodeHintType?.POSSIBLE_FORMATS && Array.isArray(formats)) {
        hints.set(DecodeHintType.POSSIBLE_FORMATS, formats.filter(Boolean));
      }
      if (DecodeHintType?.TRY_HARDER) {
        hints.set(DecodeHintType.TRY_HARDER, true);
      }
      if (DecodeHintType?.ALSO_INVERTED) {
        hints.set(DecodeHintType.ALSO_INVERTED, true);
      }
      hintsRef.current = hints;

      const reader = new BrowserMultiFormatReader(hints, captureInterval);
      reader.timeBetweenDecodingAttempts = timeBetweenDecodingAttempts;
      readerRef.current = reader;
    } else if (
      hintsRef.current &&
      typeof readerRef.current.setHints === "function"
    ) {
      readerRef.current.setHints(hintsRef.current);
    }

    return readerRef.current;
  }, [captureInterval, formats, timeBetweenDecodingAttempts]);

  const stopInternal = useCallback(
    ({ preserveError = true } = {}) => {
      const controls = readerControlsRef.current;
      readerControlsRef.current = null;

      if (controls?.stop) {
        try {
          const stopResult = controls.stop();
          if (stopResult && typeof stopResult.then === "function") {
            stopResult.catch((err) =>
              console.warn("[camera-scanner] controls stop failed", err)
            );
          }
        } catch (err) {
          console.warn("[camera-scanner] controls stop failed", err);
        }
      }

      if (readerRef.current?.reset) {
        try {
          readerRef.current.reset();
        } catch (err) {
          console.warn("[camera-scanner] reader reset failed", err);
        }
      }

      const videoElement = videoRef.current;
      if (videoElement?.srcObject) {
        const tracks = videoElement.srcObject.getTracks();
        tracks.forEach((track) => {
          try {
            track.stop();
          } catch (err) {
            console.warn("[camera-scanner] track stop failed", err);
          }
        });
        videoElement.srcObject = null;
      }

      lastResultRef.current = null;
      setScanningState(false);
      if (!preserveError) {
        clearError();
      }
    },
    [clearError, setScanningState]
  );

  const buildConstraints = useCallback(
    (deviceId) => {
      const base = constraints || DEFAULT_CONSTRAINTS;
      const videoConstraints =
        base.video && typeof base.video === "object" ? { ...base.video } : {};

      const nextConstraints = {
        audio: base.audio ?? false,
        video: videoConstraints,
      };

      if (deviceId && deviceId !== "default") {
        const { facingMode, ...rest } = videoConstraints || {};
        nextConstraints.video = {
          ...rest,
          deviceId: { exact: deviceId },
        };
      }

      return nextConstraints;
    },
    [constraints]
  );

  const start = useCallback(async () => {
    if (!active) return false;
    if (scanningRef.current) return true;

    if (!navigator?.mediaDevices?.getUserMedia) {
      notifyError("camera_not_supported");
      return false;
    }

    try {
      clearError();
      const reader = ensureReader();
      await updateCameraOptions();

      if (videoRef.current) {
        videoRef.current.setAttribute("playsinline", "true");
      }

      const activeCameraId = selectedCameraRef.current;
      const constraintsToUse = buildConstraints(activeCameraId);
      setScanningState(true);

      const scanCallback = (result, err) => {
        if (result) {
          const text =
            typeof result.getText === "function"
              ? result.getText()
              : result.text;
          if (!text) {
            return;
          }
          if (text === lastResultRef.current) {
            return;
          }
          lastResultRef.current = text;
          stopInternal({ preserveError: true });
          if (typeof onScan === "function") {
            try {
              onScan(text, { source: "camera", rawResult: result });
            } catch (callbackError) {
              console.error(
                "[camera-scanner] onScan callback failed",
                callbackError
              );
            }
          }
          return;
        }

        if (err && !PASSIVE_DECODE_ERRORS.has(err.name)) {
          console.warn("[camera-scanner] decode error", err);
        }
      };

      let controlsResult;
      if (typeof reader.decodeFromConstraints === "function") {
        controlsResult = reader.decodeFromConstraints(
          constraintsToUse,
          videoRef.current,
          scanCallback
        );
      } else {
        const deviceId =
          activeCameraId && activeCameraId !== "default"
            ? activeCameraId
            : undefined;
        controlsResult = reader.decodeFromVideoDevice(
          deviceId || null,
          videoRef.current,
          scanCallback
        );
      }

      if (controlsResult && typeof controlsResult.then === "function") {
        try {
          readerControlsRef.current = await controlsResult;
        } catch (err) {
          console.warn(
            "[camera-scanner] acquiring reader controls failed",
            err
          );
        }
      } else if (controlsResult) {
        readerControlsRef.current = controlsResult;
      }

      return true;
    } catch (err) {
      console.error("[camera-scanner] start failed", err);
      stopInternal({ preserveError: true });
      const key = ERROR_NAME_TO_KEY[err?.name] || "camera_open_failed";
      notifyError(key, err);
      return false;
    }
  }, [
    active,
    buildConstraints,
    clearError,
    ensureReader,
    notifyError,
    onScan,
    stopInternal,
    updateCameraOptions,
  ]);

  const handleCameraSelectionChange = useCallback(
    (event) => {
      const nextId = event?.target?.value || "default";
      if (!isControlled) {
        setSelectedCameraIdState(nextId);
      }
      clearError();
      if (typeof onCameraChange === "function") {
        try {
          onCameraChange(nextId);
        } catch (err) {
          console.error("[camera-scanner] onCameraChange callback failed", err);
        }
      }
      if (scanningRef.current) {
        stopInternal({ preserveError: true });
        window.setTimeout(() => {
          void start();
        }, 0);
      }
    },
    [clearError, isControlled, onCameraChange, start, stopInternal]
  );

  useEffect(() => {
    if (!active) {
      stopInternal();
      return;
    }
    void updateCameraOptions();
  }, [active, stopInternal, updateCameraOptions]);

  useEffect(
    () => () => {
      stopInternal({ preserveError: true });
    },
    [stopInternal]
  );

  useImperativeHandle(
    ref,
    () => ({
      start,
      stop: () => {
        stopInternal();
      },
      clearError,
      refreshDevices: () => updateCameraOptions(),
      isScanning: () => scanningRef.current,
      getSelectedCameraId: () => selectedCameraRef.current,
      setSelectedCameraId: (value) => {
        const nextId = value || "default";
        if (!isControlled) {
          setSelectedCameraIdState(nextId);
        }
        if (typeof onCameraChange === "function") {
          try {
            onCameraChange(nextId);
          } catch (err) {
            console.error(
              "[camera-scanner] onCameraChange callback failed",
              err
            );
          }
        }
      },
      videoElement: () => videoRef.current,
    }),
    [
      clearError,
      isControlled,
      onCameraChange,
      start,
      stopInternal,
      updateCameraOptions,
    ]
  );

  const containerClasses = useMemo(() => {
    const base = cardClass("space-y-4");
    if (!autoHide) {
      return cn(base, className);
    }
    return cn(scanning ? "space-y-4" : "hidden", base, className);
  }, [autoHide, className, scanning]);

  return (
    <>
      <div id={containerId} className={containerClasses}>
        {allowCameraSelection && cameraOptions.length > 0 ? (
          <div className="space-y-1">
            <label className={labelClass()} htmlFor={selectId}>
              {resolvedLabels.camera}
            </label>
            <select
              id={selectId}
              value={currentSelectedCameraId}
              onChange={handleCameraSelectionChange}
              className={inputClass()}
            >
              <option value="default">{resolvedLabels.cameraAuto}</option>
              {cameraOptions.map((camera, index) => (
                <option key={camera.deviceId || index} value={camera.deviceId}>
                  {camera.label || `${resolvedLabels.camera} ${index + 1}`}
                </option>
              ))}
            </select>
          </div>
        ) : null}
        <video
          id={videoId}
          ref={videoRef}
          playsInline
          className={cn("w-full rounded-xl", videoClassName)}
        />
        <div
          className={cn(
            "flex items-center justify-between gap-3",
            controlsClassName
          )}
        >
          {resolvedLabels.hint ? (
            <span className={cn(mutedTextClass(), hintClassName)}>
              {resolvedLabels.hint}
            </span>
          ) : (
            <span className={mutedTextClass()} aria-hidden="true" />
          )}
          <button
            id={closeButtonId}
            type="button"
            className={iconButtonClass()}
            onClick={() => stopInternal()}
            aria-label={resolvedLabels.cancel}
            title={resolvedLabels.cancel}
          >
            <i className="fa-solid fa-xmark" aria-hidden="true" />
          </button>
        </div>
      </div>
      {cameraError ? (
        <p
          className={cn(
            mutedTextClass(),
            "text-xs text-red-600 dark:text-red-400",
            errorClassName
          )}
        >
          {cameraError}
        </p>
      ) : null}
    </>
  );
});

export default CameraBarcodeScanner;
