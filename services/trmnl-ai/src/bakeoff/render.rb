up = Hanami.app["aspects.screens.upserter"]
Dir["/tmp/bakeoff/*.html"].sort.each do |f|
  slug = File.basename(f, ".html")
  html = %(<div class="screen screen--og_plus screen--2bit screen--landscape screen--md screen--density-1x">) + File.read(f) + "</div>"
  r = up.call(model_id: 12, name: "bakeoff_#{slug}", label: "Bakeoff #{slug}", content: html)
  puts "RESULT #{slug} #{r.class}"
end
