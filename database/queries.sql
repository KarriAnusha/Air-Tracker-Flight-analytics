SELECT 
    a.model,
    COUNT(f.flight_id) AS total_flights
FROM flights f
JOIN aircraft a 
    ON f.aircraft_registration = a.registration
GROUP BY a.model
ORDER BY total_flights DESC;

SELECT 
    a.registration,
    a.model,
    COUNT(f.flight_id) AS flight_count
FROM flights f
JOIN aircraft a 
    ON f.aircraft_registration = a.registration
GROUP BY a.registration, a.model
HAVING COUNT(f.flight_id) > 5;

SELECT 
    ap.name,
    COUNT(f.flight_id) AS outbound_flights
FROM flights f
JOIN airport ap 
    ON f.origin_iata = ap.iata_code
GROUP BY ap.name
HAVING COUNT(f.flight_id) > 5;

SELECT 
    ap.name,
    ap.city,
    COUNT(f.flight_id) AS arrival_count
FROM flights f
JOIN airport ap 
    ON f.destination_iata = ap.iata_code
GROUP BY ap.name, ap.city
ORDER BY arrival_count DESC
LIMIT 3;

SELECT 
    f.flight_number,
    o.country AS origin_country,
    d.country AS destination_country,
    CASE 
        WHEN o.country = d.country THEN 'Domestic'
        ELSE 'International'
    END AS flight_type
FROM flights f
JOIN airport o ON f.origin_iata = o.iata_code
JOIN airport d ON f.destination_iata = d.iata_code;

SELECT 
    f.flight_number,
    f.aircraft_registration,
    ap.name AS departure_airport,
    f.actual_arrival
FROM flights f
JOIN airport ap 
    ON f.origin_iata = ap.iata_code
WHERE f.destination_iata = 'DEL'
ORDER BY f.actual_arrival DESC
LIMIT 5;

SELECT 
    ap.name
FROM airport ap
LEFT JOIN flights f 
    ON ap.iata_code = f.destination_iata
WHERE f.flight_id IS NULL;

SELECT 
    airline_code,
    COUNT(CASE WHEN status = 'On Time' THEN 1 END) AS on_time,
    COUNT(CASE WHEN status = 'Delayed' THEN 1 END) AS delayed,
    COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) AS cancelled
FROM flights
GROUP BY airline_code;

SELECT 
    f.flight_number,
    f.aircraft_registration,
    o.name AS origin_airport,
    d.name AS destination_airport,
    f.scheduled_departure
FROM flights f
JOIN airport o ON f.origin_iata = o.iata_code
JOIN airport d ON f.destination_iata = d.iata_code
WHERE f.status = 'Cancelled'
ORDER BY f.scheduled_departure DESC;

SELECT 
    f.origin_iata,
    f.destination_iata,
    COUNT(DISTINCT a.model) AS model_count
FROM flights f
JOIN aircraft a 
    ON f.aircraft_registration = a.registration
GROUP BY f.origin_iata, f.destination_iata
HAVING COUNT(DISTINCT a.model) > 2;

SELECT 
    d.name AS destination_airport,
    ROUND(
        100.0 * SUM(CASE WHEN f.status = 'Delayed' THEN 1 ELSE 0 END) 
        / COUNT(f.flight_id), 2
    ) AS delay_percentage
FROM flights f
JOIN airport d 
    ON f.destination_iata = d.iata_code
GROUP BY d.name
ORDER BY delay_percentage DESC;







