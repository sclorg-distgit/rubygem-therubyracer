%{?scl:%scl_package rubygem-%{gem_name}}
%{!?scl:%global pkg_name %{name}}

%global gem_name therubyracer

%global majorver 0.11.0
%global release 6
#%%global preminorver beta5
%global fullver %{majorver}%{?preminorver}

%{?preminorver:%global gem_instdir %{gem_dir}/gems/%{gem_name}-%{fullver}}
%{?preminorver:%global gem_extdir %{_libdir}/gems/exts/%{gem_name}-%{fullver}}
%{?preminorver:%global gem_docdir %{gem_dir}/doc/%{gem_name}-%{fullver}}
%{?preminorver:%global gem_spec %{gem_dir}/specifications/%{gem_name}-%{fullver}.gemspec}
%{?preminorver:%global gem_cache %{gem_dir}/cache/%{gem_name}-%{fullver}.gem}

Summary: Embed the V8 Javascript interpreter into Ruby
Name: %{?scl_prefix}rubygem-%{gem_name}
Version: %{majorver}
Release: %{?preminorver:0.}%{release}%{?preminorver:.%{preminorver}}%{?dist}
Group: Development/Languages
License: MIT
URL: http://github.com/cowboyd/therubyracer
Source0: http://rubygems.org/gems/%{gem_name}-%{version}%{?preminorver}.gem
Patch0: rubygem-therubyracer-0.11.0beta5-v8-3.14.5.8-compatibility.patch
Patch1: rubygem-therubyracer-Rescue-v8-init-require.patch

#Patch0: %{pkg_name}-0.11.1-fix-bignum-conversion.patch
Requires: %{?scl_prefix_ruby}ruby(release)
Requires: %{?scl_prefix}rubygem(ref)
Requires: %{?scl_prefix_ruby}ruby(rubygems)
Requires: %{?scl_prefix_ruby}ruby
BuildRequires: %{?scl_prefix_ruby}ruby(release)
BuildRequires: %{?scl_prefix}rubygem(ref)
BuildRequires: %{?scl_prefix}rubygem(rspec)
BuildRequires: %{?scl_prefix_ruby}rubygems-devel
BuildRequires: %{?scl_prefix_ruby}ruby-devel
# v8 missing in buildroot, adding explicit requirement
BuildRequires: v8314
%{?scl:BuildRequires: scldevel(v8)}
# some specs run "ps aux"
BuildRequires: procps
Provides: %{?scl_prefix}rubygem(%{gem_name}) = %{version}
# same as in v8
ExclusiveArch:  %{ix86} x86_64 %{arm}

%description
Call javascript code and manipulate javascript objects from ruby. Call ruby
code and manipulate ruby objects from javascript.


%package doc
Summary: Documentation for %{pkg_name}
Group: Documentation
Requires: %{?scl_prefix}%{pkg_name} = %{version}-%{release}
BuildArch: noarch

%description doc
Documentation for %{pkg_name}

%prep
%{?scl:scl enable %{scl} - << \EOF}
gem unpack %{SOURCE0}
gem spec %{SOURCE0} -l --ruby > %{gem_name}.gemspec

%setup -n %{gem_name}-%{version}%{?preminorver} -q -D -T

%patch0 -p1
%patch1 -p1

# Link v8 .so directly for now
%if 0%{?scl:1}
sed -i 's/\$LDFLAGS << " -lv8 "/\$LDFLAGS << " -l:libv8\.\so\.%{scl_v8}-3\.14\.5 "/' ext/v8/build.rb
sed -i '16i$LDFLAGS << " -L/opt/rh/%{scl_v8}/root/usr/lib64 "' ext/v8/build.rb
sed -i '16i$INCFLAGS << " -I/opt/rh/%{scl_v8}/root/usr/include "' ext/v8/build.rb
sed -i "s/find_header('v8.h')/find_header('v8.h','\/opt\/rh\/%{scl_v8}\/root\/usr\/lib64')/" ext/v8/build.rb
%endif

%{?scl:EOF}

%build
mkdir -p .%{gem_dir}
CONFIGURE_ARGS="--with-cflags='%{optflags}' $CONFIGURE_ARGS"

%{?scl:scl enable %{scl} %{scl_v8} - << \EOF}
# Be carefull, which .gemspec is taken!
gem build ../%{gem_name}.gemspec
%gem_install -n  %{gem_name}-%{version}%{?preminorver}.gem
%{?scl:EOF}

%install
mkdir -p %{buildroot}%{gem_dir}
cp -a .%{gem_dir}/* \
        %{buildroot}%{gem_dir}/

mkdir -p %{buildroot}%{gem_extdir_mri}/lib/v8
mv %{buildroot}%{gem_instdir}/lib/v8/init.so %{buildroot}%{gem_extdir_mri}/lib/v8

# Remove the binary extension sources and build leftovers.
rm -rf %{buildroot}%{gem_instdir}/ext

# remove shebang in non-executable file
sed -i '1d' %{buildroot}%{gem_instdir}/Rakefile

%check
pushd .%{gem_instdir}
# this spec doesn't test anything, only requires redjs, which is not in fedora
mv spec/redjs_spec.rb spec/redjs_spec.rb.notest

# fix the v8 version we're testing against
%{?scl:scl enable %{scl} %{scl_v8} - << \EOF}
V8_VERSION=`d8 -e "print(version())"`
%{?scl:EOF}
sed -i "s|V8::C::V8::GetVersion().*|V8::C::V8::GetVersion().should match /^${V8_VERSION}/|" spec/c/constants_spec.rb

%{?scl:scl enable %{scl} %{scl_v8} - << \EOF}
# skip the threading specs for now
# https://github.com/cowboyd/therubyracer/pull/98#issuecomment-14442089
rspec spec --tag ~threads
%{?scl:EOF}
popd

%files
%dir %{gem_instdir}
%doc %{gem_instdir}/README.md
%{gem_libdir}
%{gem_extdir_mri}
%exclude %{gem_cache}
%exclude %{gem_instdir}/.*
%{gem_spec}

%files doc
%doc %{gem_docdir}
%doc %{gem_instdir}/Changelog.md
%{gem_instdir}/benchmarks.rb
%{gem_instdir}/Gemfile
%{gem_instdir}/Rakefile
%{gem_instdir}/spec
%{gem_instdir}/thefrontside.png
%{gem_instdir}/therubyracer.gemspec

%changelog
* Thu Mar 20 2014 Josef Stribny <jstribny@redhat.com> - 0.11.0-6
- Depend on scldevel(v8) virtual provide
  - Resolves: rhbz#1070329

* Mon Feb 17 2014 Josef Stribny <jstribny@redhat.com> - 0.11.0-5
- Don't install v8 scl macros, they should come in v8 scldevel subpackage
  - Related: rhbz#1055544

* Thu Feb 13 2014 Josef Stribny <jstribny@redhat.com> - 0.11.0-4
- Add intuitive error report when v8 SCL is not enabled
  - Resolves: rhbz#1060701

* Tue Nov 26 2013 Josef Stribny <jstribny@redhat.com> - 0.11.0-3
- Create macros for v8

* Mon Nov 11 2013 Josef Stribny <jstribny@redhat.com> - 0.11.0-2
- Depend on v8 scl

* Mon May 20 2013 Josef Stribny <jstribny@redhat.com> - 0.11.0-1
- Rebuild for https://fedoraproject.org/wiki/Features/Ruby_2.0.0
- Update to therubyracer 0.11.0

* Fri May 10 2013 Josef Stribny <jstribny@redhat.com> - 0.11.0-0.6.beta5
- Rebuild for https://fedoraproject.org/wiki/Features/Ruby_2.0.0
- Update to 0.11.0
- Add patch that fixes bignum operations on Ruby 2.0.

* Thu May 02 2013 Vít Ondruch <vondruch@redhat.com> - 0.11.0-0.5.beta5
- Fix compatibility with v8-3.14.5.8.

* Thu Jul 26 2012 Bohuslav Kabrda <bkabrda@redhat.com> - 0.11.0-0.4.beta5
- Rebuilt for SCL.

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.11.0-0.3.beta5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Mon Jul 16 2012 Bohuslav Kabrda <bkabrda@redhat.com> - 0.11.0-0.2.beta5
- Fixed minor issues according to review comments (RHBZ #838870).

* Fri Jun 15 2012 Bohuslav Kabrda <bkabrda@redhat.com> - 0.11.0-0.1.beta5
- Initial package
