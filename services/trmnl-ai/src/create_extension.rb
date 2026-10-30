# Creates the Terminus poll extension "AI Board" (run once):
#   docker exec -i terminus bundle exec hanami console < create_extension.rb
tpl = <<~LIQUID
  {%- comment -%} HTML is designed by trmnl-ai (LLM). See services/trmnl-ai in the second brain. {%- endcomment -%}
  <div class="{{ extension.css_classes }}">{{ source_1.html }}</div>
LIQUID
e = Hanami.app["repositories.extension"].create(
  name: "ai_board", label: "AI Board",
  description: "LLM-designed screen from trmnl-ai (weather, TfL lines, commute, station + planned disruptions).",
  kind: "poll", tags: ["commute", "ai"], template: tpl, interval: 10, unit: "minute", mode: "light",
  start_at: Time.utc(2026, 10, 30)
)
Hanami.app["repositories.extension_exchange"].create(extension_id: e.id, verb: "get", template: "http://trmnl-ai:8080/screen.json")
Hanami.app["repositories.extension_model"].create(extension_id: e.id, model_id: 12)
puts "EXTENSION_ID=#{e.id}"
