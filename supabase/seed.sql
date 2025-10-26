-- Seed data for testing the costume classifier dashboard
-- This creates sample sightings to verify the dashboard UI works correctly

-- Insert sample costume detections with realistic descriptions
insert into public.sightings (description, confidence, timestamp) values
  ('witch with purple hat and broom', 0.92, now() - interval '2 hours'),
  ('skeleton with glowing bones', 0.88, now() - interval '1 hour 55 minutes'),
  ('superhero in red cape', 0.85, now() - interval '1 hour 50 minutes'),
  ('inflatable T-Rex dinosaur', 0.95, now() - interval '1 hour 45 minutes'),
  ('pirate with eye patch and parrot', 0.91, now() - interval '1 hour 40 minutes'),
  ('homemade cardboard robot with LED lights', 0.78, now() - interval '1 hour 35 minutes'),
  ('princess in pink dress with tiara', 0.94, now() - interval '1 hour 30 minutes'),
  ('zombie with torn clothes and fake blood', 0.89, now() - interval '1 hour 25 minutes'),
  ('black cat with whiskers and tail', 0.87, now() - interval '1 hour 20 minutes'),
  ('astronaut in white suit with helmet', 0.93, now() - interval '1 hour 15 minutes'),
  ('vampire with cape and fangs', 0.90, now() - interval '1 hour 10 minutes'),
  ('ninja in all black outfit', 0.86, now() - interval '1 hour 5 minutes'),
  ('ghost in white sheet with eye holes', 0.82, now() - interval '1 hour'),
  ('mummy wrapped in bandages', 0.88, now() - interval '55 minutes'),
  ('Barbie and Ken duo', 0.91, now() - interval '50 minutes'),
  ('Spider-Man with web shooters', 0.94, now() - interval '45 minutes'),
  ('doctor in white coat with stethoscope', 0.85, now() - interval '40 minutes'),
  ('unicorn with rainbow mane and horn', 0.89, now() - interval '35 minutes'),
  ('pumpkin costume with stem hat', 0.87, now() - interval '30 minutes'),
  ('cowboy with hat and lasso', 0.90, now() - interval '25 minutes');
