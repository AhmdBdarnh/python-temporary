import { useState, useEffect } from 'react';

// Function to fetch data from the API
const fetchChartData = async (country = 'ISR', date = '2024-08-23') => {
  try {
    const response = await fetch(`http://localhost:8005/charts?date=${date}`);
    if (!response.ok) {
      throw new Error('Failed to fetch data');
    }
    const data = await response.json();
    return data.charts[country] || [];
  } catch (error) {
    console.error('Error fetching chart data:', error);
    return [];
  }
};

const useCountryData = () => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [date, setDate] = useState('-1'); // Update this as needed

  useEffect(() => {
    // Fetch the data when the component mounts
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchChartData();
        setChartData(data);
        if (data.length > 0) {
          setDate(data[0].distribution_date); // Set the date from the fetched data
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  return {
    name: "Israel", // Assuming this is static; adjust as needed
    date,
    chart: chartData,
    loading,
    error,
  };
};

export default useCountryData;
