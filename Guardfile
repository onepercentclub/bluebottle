ignore /^node_modules|docs|dist|env|build.*?/
filter /\.txt|zip|egg|pyc|js|css|hbs|html$/

notification :on
interactor :on

def python_unittest(app=nil, test_name=nil)
  # Some apps to ignore
  ignored_apps = ['test', 'auth', 'settings', 'test_files']
  return if ignored_apps.include? app

  path = []
  unless app.nil? && test_name.nil?
    path.push 'bluebottle'
    path.push app unless app.nil?
    path.push "tests.#{test_name}" unless test_name.nil?
  end

  cmd = "python manage.py test #{path.join('.')}"
  puts "Executing #{cmd}"

  `#{cmd}`
end

watch /.*/ do |m|
  puts "Changed #{m[0]}..."
end

group :django do
  group :single_tests do
    guard :shell do
      # Run the whole test suite for the app when a py file changes.
      watch /^bluebottle\/(.*)\/([a-z|_]+).py$/ do |m|
        unless m[1].to_s.include? 'test'
          puts "Matched #{m[0]}..."

          python_unittest m[1]
        end
      end
      
      # Run the whole test suite when the test app changes.
      watch /^bluebottle\/test\/(.*).py$/ do |m|
        puts "Matched #{m[0]}..."
        python_unittest
      end

      # Run only the changed test module when the test py file changes.
      watch /^bluebottle\/([a-z|_]+)\/tests\/(test_([a-z|_]+)).py$/ do |m|
        puts "Matched #{m[0]}..."
        python_unittest m[1], m[2]
      end
    end
  end

  group :full_tests do
    guard :shell, :all_on_start => true do
      # Run the whole test suite for the project when the manage.py file 
      # changes or guard is run for the first time.
      watch %r{^manage.py$} do |m|
        puts "Matched #{m[0]}..."
        python_unittest
      end
    end
  end
end