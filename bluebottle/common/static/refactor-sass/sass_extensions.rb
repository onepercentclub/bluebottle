require "sass"
require "erb"

module Sass::Script::Functions
  def self.included(base)
    if base.respond_to?(:declare)
      base.declare :inline_svg, [:file, :col1, :col2]
    end
  end

  # Read an external SVG file and import it as string.
  def inline_svg(file,col1,col2)
    assert_type file, :String, :file
    assert_type col1, :String, :col1
    assert_type col2, :String, :col2

    file = file.value
    col1 = col1.value
    col2 = col2.value

    path = '/images/'

    # root = options[:filesystem_importer].new(".").to_s
    root = File.dirname(__FILE__).to_s

    real_path = File.expand_path(File.join(root, path, file))

    svgStr = data(real_path)

    svgStr = svgStr.strip.gsub(/>\s+</, "><")
    
    svgStr.sub! col1, col2

    data = [svgStr].flatten.pack("m0") # base64
    # data = svgStr.gsub(/#/, "%23") # raw
    # preData = %q(url\('data:image/svg+xml;charset=UTF-8,)
    preData = %q(url\('data:image/svg+xml;charset=utf-8;base64,)
    postData = %q('\));

    Sass::Script::String.new(preData + data + postData);

  end

private

  def data(path)
    if File.readable?(path)
      File.open(path, "rb") {|io| io.read}
    else
      raise "File not found or cannot be read: #{path}"
    end
  end

end
