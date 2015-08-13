START TRANSACTION;

DELETE FROM resource_review_score;

-- Get top-level rating information
INSERT INTO
	resource_review_score
(
	resource_id,
	population_id,
	num_ratings,
	first_reviewed,
	last_reviewed,
	rating_avg,
	staff_rating_avg,
	intake_rating_avg
)
SELECT
	res.id,
	0, -- Special value used for top-level scores
	COUNT(1),
	MIN(rev.date_created),
	MAX(rev.date_created),
	AVG(rev.rating),
	AVG(rev.intake_rating),
	AVG(rev.staff_rating)
FROM
	resource res
	INNER JOIN review rev On res.id = rev.resource_id
WHERE
	rev.visible = 1
	AND rev.is_old_review = 0	
GROUP BY
	res.id;

-- Get aggregated information per provider per population
INSERT INTO
	resource_review_score
(
	resource_id,
	population_id,
	num_ratings,
	first_reviewed,
	last_reviewed,	
	rating_avg,
	staff_rating_avg,
	intake_rating_avg
)
SELECT
	res.id,
	up.population_id,
	COUNT(rev.id),
	MIN(rev.date_created),
	MAX(rev.date_created),	
	AVG(rev.rating),
	AVG(rev.intake_rating),
	AVG(rev.staff_rating)	
FROM
	resource res
	INNER JOIN review rev On res.id = rev.resource_id
	INNER JOIN user u On rev.user_id = u.id
	INNER JOIN userpopulation up On u.id = up.user_id
WHERE
	rev.visible = 1
	AND rev.is_old_review = 0
GROUP BY
	res.id,
	up.population_id;

COMMIT;
