import { useEffect, useState } from 'react';

/**
 * Returns a debounced version of the provided value.
 *
 * The debounced value only updates after the specified delay has elapsed
 * without the input value changing again. Useful for delaying expensive
 * operations such as API calls triggered by user input.
 *
 * @template T
 * @param {T} value - The value to debounce.
 * @param {number} [delay=300] - Delay in milliseconds before updating.
 * @returns {T} The debounced value.
 */
export default function useDebouncedValue(value, delay = 300) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      window.clearTimeout(timeoutId);
    };
  }, [value, delay]);

  return debouncedValue;
}
